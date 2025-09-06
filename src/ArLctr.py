#  src/ArLctr.py

import json
import logging
import os

from dataclasses import dataclass

import numpy as np
import cv2
from sklearn.cluster import KMeans

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


class AreaLocator:
    def __init__(self):
        self.resource_path = "resources"
        json_path = os.path.join(self.resource_path, "config.json")
        with open(json_path, "r", encoding="utf-8") as f:
            self.config = json.load(f)

    def get_templates(self, names: list[str]) -> list[Template]:
        lang = self.config["language"]
        names = names or self.config["templates"]
        tmpls = []
        for name in names:
            if name not in self.config["templates"]:
                log.warning(f"Template '{name}' not found in 'templates' of config")
                continue

            path = os.path.join(self.resource_path, "templates", lang, f"{name}.png")
            if not os.path.exists(path):
                log.warning(f"Template '{name}' not found at '{path}'")
                continue

            tmpl = self.config["templates"][name]
            tmpls.append(Template(name=str(tmpl.get("name", name)),
                                  path=str(path),
                                  weight=float(tmpl.get("weight", 1)),
                                  area=tuple(tmpl.get("area", self.config["region"]),)))

        tmpls.sort(key=lambda x: x.weight, reverse=True)
        return tmpls

    # def get_ocr_area(self, key: str) -> OCRArea:
    #     if key not in self.config["areas"]:
    #         raise ValueError(f"Area {key} not found in 'areas' of config")

    #     ocr_area: dict = self.config["areas"][key]
    #     return OCRArea(name=str(ocr_area.get("name", key)),
    #                    area=tuple(ocr_area.get("area", self.config["region"])),
    #                    expects=["null"],)

    def match_template(self, screen: np.ndarray, names: list[str] = [], show: bool = False) -> Match:
        best_match = {"name": "unknown", "loc": [0, 0, 0, 0], "val": 0.65}
        for tmpl in self.get_templates(names):
            x, y, w, h = tmpl.area
            roi = screen[y:y + h, x:x + w]
            img_tmpl = cv2.imread(tmpl.path, cv2.IMREAD_COLOR)
            result = cv2.matchTemplate(roi, img_tmpl, cv2.TM_CCOEFF_NORMED)
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

            if max_val >= best_match["val"]:
                loc = (x + max_loc[0], y + max_loc[1], img_tmpl.shape[1], img_tmpl.shape[0])
                best_match = {"name": tmpl.name, "loc": loc, "val": max_val}
            if max_val >= self.config["match_threshold"]:
                break

        name = best_match["name"]
        log.info(f"Matched {name}")

        # show match result to debug
        if best_match["val"] <= 0.7 or show:
            display_image = screen.copy()

            # draw all templates
            if name == "unknown":
                for tmpl in self.get_templates(names):
                    x, y, w, h = tmpl.area
                    cv2.rectangle(display_image, (x, y), (x + w, y + h), (0, 255, 0), 3)

            # draw matched template
            else:
                loc = best_match["loc"]
                top_left = (loc[0], loc[1])
                bottom_right = (loc[0] + loc[2], loc[1] + loc[3])
                cv2.rectangle(display_image, top_left, bottom_right, (0, 0, 255), 3)

            # show
            cv2.imshow(f"{name}", display_image)
            cv2.waitKey(5000)
            cv2.destroyAllWindows()

        return Match(**best_match)

    def search_reds(self, screen: np.ndarray, show: bool = False) -> list[tuple[int, int]] | None:
        bigmap = self.config["areas"]["bigmap"]
        area = bigmap["area"]
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

        show = True  # debug

        # show result
        if show:
            dsp = screen.copy()
            for c in centers:
                cv2.circle(dsp, c, 5, (0, 0, 255), -1)
            cv2.imshow("reds on bigmap", dsp)
            cv2.waitKey(5000)
            cv2.destroyAllWindows()

        return centers
