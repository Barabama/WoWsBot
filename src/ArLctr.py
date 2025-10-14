#  src/ArLctr.py

import json
import logging
import os
import threading

from collections import defaultdict
from dataclasses import dataclass

import numpy as np
import cv2
from sklearn.cluster import KMeans
from ultralytics import YOLO

log = logging.getLogger(__name__)


@dataclass
class Template:
    name: str
    path: str
    weight: float
    area: tuple[int, int, int, int]


@dataclass
class Match:
    name: str
    loc: tuple[int, int, int, int]
    val: float
    area: tuple[int, int, int, int]
    roi: np.ndarray
    screen: np.ndarray


class AreaLocator:
    def __init__(self):
        self.resource_path = "resources"
        json_path = os.path.join(self.resource_path, "config.json")
        user_path = os.path.join(self.resource_path, "user.json")
        models_path = os.path.join(self.resource_path, "models")
        templates_path = os.path.join(self.resource_path, "templates")

        self.config = self.load_config(json_path)
        self.user = self.load_user(user_path)
        self.templates = self.load_templates(templates_path)
        self.model_compass = self.load_model(models_path, self.config["model_compass"])
        self.model_minimap = self.load_model(models_path, self.config["model_minimap"])
        self.model_warship = self.load_model(models_path, self.config["model_warship"])

    def load_config(self, json_path: str) -> dict:
        """Load configuration from JSON file"""
        if not os.path.exists(json_path):
            raise FileNotFoundError(f"'config.json' not found at {json_path}")
        with open(json_path, "r", encoding="utf-8") as f:
            config = json.load(f)
        required_keys = ["region", "positions", "areas", "templates"]
        missing_keys = [key for key in required_keys if key not in config]
        if missing_keys:
            raise ValueError(f"Missing keys in config.json, {missing_keys}")
        return config

    def load_user(self, user_path: str) -> dict:
        """Load user configuration from JSON file"""
        if not os.path.exists(user_path):
            raise FileNotFoundError(f"'user.json' not found at {user_path}")
        with open(user_path, "r", encoding="utf-8") as f:
            user = json.load(f)
        required_keys = ["language", "title", "scheduled_tasks"]
        missing_keys = [key for key in required_keys if key not in user]
        if missing_keys:
            raise ValueError(f"Missing keys in user.json, {missing_keys}")
        return user

    def load_templates(self, templates_path: str) -> dict[str, Template]:
        """Load templates from the templates directory"""
        language: str = self.user["language"]
        templates: dict[str, dict] = self.config["templates"]
        tmpls = {}
        for key, tmpl in templates.items():
            name = str(tmpl.get("name", key))
            path = os.path.join(templates_path, language, f"{name}.png")
            if not os.path.exists(path):
                log.warning(f"Template {name} not found at {path}")
                continue
            weight = float(tmpl.get("weight", 1.0))
            area = tuple(map(int, tmpl.get("area", self.config["region"])))
            if len(area) != 4:
                log.warning(f"Area for template {name} is not 4-int list")
                continue
            tmpls[name] = Template(name=name, path=path, weight=weight, area=area)
        return tmpls

    def load_model(self, models_path: str, name: str) -> YOLO | None:
        """Load a YOLO model from the models directory"""
        path = os.path.join(models_path, name)
        if os.path.exists(path):
            log.info(f"Loaded model {name}")
            return YOLO(path)
        else:
            log.warning(f"Model {name} not found")
            return None

    def get_templates(self, names: list[str]) -> list[Template]:
        """Get sorted templates by names or all templates if names is empty"""
        names = names or list(self.templates.keys())
        tmpls = []
        for name in names:
            if name not in self.config["templates"]:
                log.warning(f"Template '{name}' not found in 'templates' of config")
                continue
            tmpls.append(self.templates[name])

        tmpls.sort(key=lambda x: x.weight, reverse=True)
        return tmpls

    def _show_window(self, name: str, loc: tuple[int, int], image: np.ndarray):
        """Display an image in a named OpenCV window"""
        def show_image():
            # Use a default window name if name is "unknown" to avoid OpenCV errors
            window_name = "result" if name == "unknown" else name
            cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
            cv2.setWindowProperty(window_name, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
            height, width = image.shape[:2]
            cv2.resizeWindow(window_name, width, height)
            cv2.moveWindow(window_name, loc[0], loc[1])
            try:
                cv2.setWindowProperty(window_name, cv2.WND_PROP_TOPMOST, 1)
            except AttributeError:
                pass
            cv2.imshow(window_name, image)
            cv2.waitKey(3000)
            cv2.destroyWindow(window_name)

        thread = threading.Thread(target=show_image, daemon=True)
        thread.start()
        thread.join(timeout=3)

    def _draw_overlay(self, screen: np.ndarray, elems: list[tuple[str, tuple]]) -> np.ndarray:
        """
        Draw overlay elements with transparent background
        This creates a truly transparent background where only the drawn elements are visible
        """
        overlay = np.zeros((screen.shape[0], screen.shape[1], 4), dtype=np.uint8)

        for elem, params in elems:
            if elem == "rectangle":
                x, y, w, h, color, thickness = params
                cv2.rectangle(overlay, (x, y), (x + w, y + h), (*color, 255), thickness)
            elif elem == "circle":
                cx, cy, r, color, thickness = params
                cv2.circle(overlay, (cx, cy), r, (*color, 255), thickness)
            elif elem == "line":
                x1, y1, x2, y2, color, thickness = params
                cv2.line(overlay, (x1, y1), (x2, y2), (*color, 255), thickness)

        mask = overlay[:, :, 3]
        mask_inv = cv2.bitwise_not(mask)

        background = cv2.bitwise_and(screen, screen, mask=mask_inv)

        foreground = overlay[:, :, :3]
        foreground = cv2.bitwise_and(foreground, foreground, mask=mask)

        result = cv2.add(background, foreground)
        return result

    def match_template(self, screen: np.ndarray, names: list[str] | None = None,
                       show: bool = False) -> Match:
        """Match template on screen and return the best match"""
        if names is None:
            names = []

        threshold = self.config.get("match_threshold", 0.7)
        match = Match(name="unknown", loc=(0, 0, 0, 0), val=0.65, area=(0, 0, 0, 0),
                      roi=screen, screen=screen)

        for tmpl in self.get_templates(names):
            x, y, w, h = tmpl.area
            roi = screen[y:y + h, x:x + w]
            img_tmpl = cv2.imread(tmpl.path, cv2.IMREAD_COLOR)
            if img_tmpl is None:
                log.warning(f"Template '{tmpl.name}' not found at '{tmpl.path}'")
                continue

            result = cv2.matchTemplate(roi, img_tmpl, cv2.TM_CCOEFF_NORMED)
            val_min, val_max, loc_min, loc_max = cv2.minMaxLoc(result)

            if val_max >= match.val:
                loc = (x + loc_max[0], y + loc_max[1], img_tmpl.shape[1], img_tmpl.shape[0])
                match = Match(name=tmpl.name, loc=loc, val=val_max, area=tmpl.area, roi=roi, screen=screen)
            if val_max >= threshold:
                break

        name = match.name
        log.info(f"Matched {name}")

        # Show match result to debug
        if match.val <= threshold or show:

            # Draw all templates
            if name == "unknown":
                elems = [("rectangle", (*tmpl.area, (0, 255, 0), 3))
                         for tmpl in self.get_templates(names)]
            # Draw matched template
            else:
                elems = [("rectangle", (*match.loc, (0, 0, 255), 3))]

            # Show
            overlay = self._draw_overlay(screen=match.roi, elems=elems)
            self._show_window(name=name, loc=match.area[:2], image=overlay)

        return match

    def read_bigmap(self, screen: np.ndarray, show: bool = False) -> list[tuple[int, int]] | None:
        """Read bigmap and return red point coordinates"""
        # Validate area configuration
        if "bigmap" not in self.config["areas"]:
            log.error("Bigmap area not configured")
            return None

        area = self.config["areas"]["bigmap"]["area"]
        x, y, w, h = area
        roi = screen[y:y + h, x:x + w]

        # Find all red points
        hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
        red1_lower = np.array([0, 200, 200])
        red1_upper = np.array([9, 255, 255])
        red2_lower = np.array([170, 200, 200])
        red2_upper = np.array([179, 255, 255])
        mask1 = cv2.inRange(hsv, red1_lower, red1_upper)
        mask2 = cv2.inRange(hsv, red2_lower, red2_upper)
        mask = mask1 + mask2

        coords = np.column_stack(np.where(mask > 0))
        coords = [(int(p[1]), int(p[0])) for p in coords]
        if len(coords) <= 0:
            log.error("No red point found")
            return None

        # K-means clustering
        points = np.array(coords)
        n_clusters = min(5, max(1, len(points) // 10))
        kmeans = KMeans(n_clusters=n_clusters, random_state=0).fit(points)
        centers = kmeans.cluster_centers_
        centers = [(int(x + c[0]), int(y + c[1])) for c in centers]

        # Show result
        show = True
        if show:
            elems = [("circle", (*c, 5, (0, 0, 255), -1)) for c in centers]
            overlay = self._draw_overlay(screen=screen, elems=elems)
            self._show_window(name="bigmap", loc=(x, y), image=overlay)

        return centers

    def read_minimap(self, screen: np.ndarray, show: bool = False) -> dict[str, list[np.ndarray]] | None:
        """
        Read minimap and return ship positions and directions
        Returns: {"self": [arr(x, y), arr(dx, dy)],
                  "ally": [arr(x1, y1), arr(x2, y2),...],
                  "enemy": [arr(x1, y1), arr(x2, y2),...]}
        """
        # Validate area configuration and model availability
        if "minimap" not in self.config["areas"]:
            log.error("Minimap area not configured")
            return None

        if self.model_minimap is None:
            log.error("Minimap model not loaded")
            return None

        area = self.config["areas"]["minimap"]["area"]
        x, y, w, h = area
        roi = screen[y:y + h, x:x + w]

        # Predict
        data = defaultdict(list)
        self_conf = 0.0
        self_center = None
        self_kps = None
        result = self.model_minimap.predict(roi, conf=0.5, iou=0.5)[0]
        if result.boxes is None or result.keypoints is None:
            log.warning("No boxes or keypoints detected in minimap")
            return None

        cls_ids = result.boxes.cls.cpu().numpy()
        confs = result.boxes.conf.cpu().numpy()
        xywhs = result.boxes.xywh.cpu().numpy()
        kpts = result.keypoints.xy.cpu().numpy()
        for i in range(len(cls_ids)):
            label = result.names[int(cls_ids[i])]
            conf = confs[i]
            center = xywhs[i][:2]
            data[label].append(center)
            if label == "self" and conf > self_conf:
                self_conf = conf
                self_center = center
                self_kps = kpts[i]
        if self_kps is None:
            log.warning("No self keypoints detected in minimap")
            return None

        # Handle keypoints of self
        bow, stern, port, stbd = [p for p in self_kps[:4]]
        points = np.array([bow, self_center, stern, port, stbd])
        a, b = np.polyfit(points[:, 0], points[:, 1], 1)
        delta = np.array([1.0, a])
        data["self"] = [self_center, delta]

        show = True
        if show:
            frame = result.plot()
            self._show_window(name="minimap", loc=(x, y), image=frame)

        return dict(data)

    def read_compass(self, screen: np.ndarray, show: bool = False) -> np.ndarray | None:
        """Read compass and return direction vector"""
        # Validate area configuration and model availability
        if "compass" not in self.config["areas"]:
            log.error("Compass area not configured")
            return None

        if self.model_compass is None:
            log.error("Compass model not loaded")
            return None

        area = self.config["areas"]["compass"]["area"]
        x, y, w, h = area
        roi = screen[y:y + h, x:x + w]

        # Predict using the model
        best_conf = 0.0
        best_center = None
        best_kps = None
        result = self.model_compass.predict(roi, conf=0.5, iou=0.5)[0]
        if result.boxes is None or result.keypoints is None:
            log.warning("No boxes or keypoints detected in compass")
            return None

        cls_ids = result.boxes.cls.cpu().numpy()
        confs = result.boxes.conf.cpu().numpy()
        xywhs = result.boxes.xywh.cpu().numpy()
        kpts = result.keypoints.xy.cpu().numpy()
        for i in range(len(cls_ids)):
            label = result.names[int(cls_ids[i])]
            conf = confs[i]
            if label == "self" and conf > best_conf:
                best_conf = conf
                best_center = xywhs[i][:2]
                best_kps = kpts[i]
        if best_kps is None:
            log.warning("No self keypoints detected in compass")
            return None

        # Handle keypoints of self
        bow, port, stbd = [p for p in best_kps[:3]]
        points = np.array([bow, best_center, port, stbd])
        a, b = np.polyfit(points[:, 0], points[:, 1], 1)
        delta = np.array([1.0, a])

        show = True
        if show:
            frame = result.plot()
            self._show_window(name="compass", loc=(x, y), image=frame)

        return delta
