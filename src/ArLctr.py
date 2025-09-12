#  src/ArLctr.py

from collections import defaultdict
import json
import logging
import os

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

# @dataclass
# class OCRArea:
#     name: str
#     area: tuple[int, int, int, int]
#     expects: list[str]  # useless yet


@dataclass
class Match:
    name: str
    loc: tuple[int, int, int, int]
    val: float
    screen: np.ndarray


@dataclass
class MapData:
    self: list[tuple[int, int]]
    ally: list[tuple[int, int]]
    enemy: list[tuple[int, int]]


class AreaLocator:
    def __init__(self):
        self.resource_path = "resources"
        json_path = os.path.join(self.resource_path, "config.json")
        models_path = os.path.join(self.resource_path, "models")
        templates_path = os.path.join(self.resource_path, "templates")

        self.config = self.load_config(json_path)
        self.templates = self.load_templates(templates_path)
        self.model_compass = self.load_model(models_path, self.config["model_compass"])
        self.model_minimap = self.load_model(models_path, self.config["model_minimap"])
        self.model_warship = self.load_model(models_path, self.config["model_warship"])

    def load_config(self, json_path: str) -> dict:
        if not os.path.exists(json_path):
            raise FileNotFoundError(f"'config.json' not found at {json_path}")
        with open(json_path, "r", encoding="utf-8") as f:
            config = json.load(f)
        required_keys = ["language", "title", "region", "positions", "areas", "templates"]
        missing_keys = [key for key in required_keys if key not in config]
        if missing_keys:
            raise ValueError(f"Missing keys in config.json, {missing_keys}")
        return config

    def load_templates(self, templates_path: str) -> dict[str, Template]:
        language: str = self.config["language"]
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
        path = os.path.join(models_path, name)
        if os.path.exists(path):
            log.info(f"Loaded model {name}")
            return YOLO(path)
        else:
            log.warning(f"Model {name} not found")
            return None

    def get_templates(self, names: list[str]) -> list[Template]:
        names = names or list(self.templates.keys())
        tmpls = []
        for name in names:
            if name not in self.config["templates"]:
                log.warning(f"Template '{name}' not found in 'templates' of config")
                continue
            tmpls.append(self.templates[name])

        tmpls.sort(key=lambda x: x.weight, reverse=True)
        return tmpls

    def _show_borderless_window(self, name: str, loc: tuple[int, int], image: np.ndarray,):
        cv2.namedWindow(name, cv2.WINDOW_NORMAL)
        cv2.setWindowProperty(name, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
        cv2.moveWindow(name, loc[0], loc[1])
        try:
            cv2.setWindowProperty(name, cv2.WND_PROP_TOPMOST, 1)
        except AttributeError:
            pass
        cv2.imshow(name, image)

    # def get_ocr_area(self, key: str) -> OCRArea:
    #     if key not in self.config["areas"]:
    #         raise ValueError(f"Area {key} not found in 'areas' of config")

    #     ocr_area: dict = self.config["areas"][key]
    #     return OCRArea(name=str(ocr_area.get("name", key)),
    #                    area=tuple(ocr_area.get("area", self.config["region"])),
    #                    expects=["null"],)

    def match_template(self, screen: np.ndarray, names: list[str] = [], show: bool = False) -> Match:
        best_match = {"name": "unknown", "loc": [0, 0, 0, 0], "val": 0.65, "screen": screen}
        for tmpl in self.get_templates(names):
            x, y, w, h = tmpl.area
            roi = screen[y:y + h, x:x + w]
            img_tmpl = cv2.imread(tmpl.path, cv2.IMREAD_COLOR)
            if img_tmpl is None:
                log.warning(f"Template '{tmpl.name}' not found at '{tmpl.path}'")
                continue

            result = cv2.matchTemplate(roi, img_tmpl, cv2.TM_CCOEFF_NORMED)
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

            if max_val >= best_match["val"]:
                loc = (x + max_loc[0], y + max_loc[1], img_tmpl.shape[1], img_tmpl.shape[0])
                best_match = {"name": tmpl.name, "loc": loc, "val": max_val, "screen": screen}
            if max_val >= self.config.get("match_threshold", 0.7):
                break

        name = best_match["name"]
        log.info(f"Matched {name}")

        # show match result to debug
        if best_match["val"] <= 0.7 or show:
            dsp = screen.copy()

            # draw all templates
            if name == "unknown":
                for tmpl in self.get_templates(names):
                    x, y, w, h = tmpl.area
                    cv2.rectangle(dsp, (x, y), (x + w, y + h), (0, 255, 0), 3)

            # draw matched template
            else:
                loc = best_match["loc"]
                top_left = (loc[0], loc[1])
                bottom_right = (loc[0] + loc[2], loc[1] + loc[3])
                cv2.rectangle(dsp, top_left, bottom_right, (0, 0, 255), 3)

            # show
            self._show_borderless_window(f"{name}", best_match["loc"][:2], dsp)
            cv2.waitKey(5000)
            cv2.destroyAllWindows()

        return Match(**best_match)

    def read_bigmap(self, screen: np.ndarray, show: bool = False) -> list[tuple[int, int]] | None:
        area = self.config["areas"]["bigmap"]["area"]
        x, y, w, h = area
        roi = screen[y:y + h, x:x + w]

        # find all red points
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

        # show result
        if show:
            dsp = screen.copy()
            for c in centers:
                cv2.circle(dsp, c, 5, (0, 0, 255), -1)
            self._show_borderless_window("bigmap", (x, y), dsp)
            cv2.waitKey(5000)
            cv2.destroyAllWindows()

        return centers

    def read_minimap(self, screen: np.ndarray) -> dict[str, list[np.ndarray]] | None:
        """
        Returns: {"self": [arr(x, y), arr(dx, dy)],
                  "ally": [arr(x1, y1), arr(x2, y2),...],
                  "enemy": [arr(x1, y1), arr(x2, y2),...]}
        """
        area = self.config["areas"]["minimap"]["area"]
        x, y, w, h = area
        roi = screen[y:y + h, x:x + w]
        if self.model_minimap is None:
            return None

        # predict
        data = defaultdict(list)
        self_conf = 0.0
        self_center = None
        self_kps = None
        result = self.model_minimap.predict(roi, conf=0.5, iou=0.5)[0]
        if result.boxes is None or result.keypoints is None:
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
            return None

        # handle keypoints of self
        bow, stern, port, stbd = [p for p in self_kps[:4]]
        points = np.array([bow, self_center, stern, port, stbd])
        a, b = np.polyfit(points[:, 0], points[:, 1], 1)
        delta = np.array([1.0, a])
        data["self"] = [self_center, delta]

        show = True
        if show:
            frame = result.plot()
            self._show_borderless_window("minimap", (x, y), frame)
            cv2.waitKey(3000)
            cv2.destroyAllWindows()

        return data

    def read_compass(self, screen: np.ndarray) -> np.ndarray | None:
        area = self.config["areas"]["compass"]["area"]
        x, y, w, h = area
        roi = screen[y:y + h, x:x + w]
        if self.model_compass is None:
            return None

        # predict
        best_conf = 0.0
        best_center = None
        best_kps = None
        result = self.model_compass.predict(roi, conf=0.5, iou=0.5)[0]
        if result.boxes is None or result.keypoints is None:
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
            return None

        # handle keypoints of self
        bow, port, stbd = [p for p in best_kps[:3]]
        points = np.array([bow, best_center, port, stbd])
        a, b = np.polyfit(points[:, 0], points[:, 1], 1)
        delta = np.array([1.0, a])

        show = True
        if show:
            frame = result.plot()
            self._show_borderless_window("compass", (x, y), frame)
            cv2.waitKey(3000)
            cv2.destroyAllWindows()

        return delta
