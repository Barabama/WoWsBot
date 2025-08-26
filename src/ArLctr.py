#  src/ArLctr.py

import json
import logging
import os

from dataclasses import dataclass

import numpy as np
import cv2

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


@dataclass
class OCRArea:
    name: str
    area: tuple[int, int, int, int]
    expects: list[str]  # useless yet


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

    def get_ocr_area(self, key: str) -> OCRArea:
        if key not in self.config["areas"]:
            raise ValueError(f"Area {key} not found in 'areas' of config")

        ocr_area: dict = self.config["areas"][key]
        return OCRArea(name=str(ocr_area.get("name", key)),
                       area=tuple(ocr_area.get("area", self.config["region"])),
                       expects=["null"],)

    def match_template(self, screen: np.ndarray, names:list[str]=[], show: bool = False) -> Match:
        best_match = {"name": "unknown", "loc": tuple(self.config["region"]), "val": 0.65}
        for tmpl in self.get_templates(names):
            x, y, w, h = tmpl.area
            roi = screen[y:y+h, x:x+w]
            img_tmpl = cv2.imread(tmpl.path, cv2.IMREAD_COLOR)
            result = cv2.matchTemplate(roi, img_tmpl, cv2.TM_CCOEFF_NORMED)
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

            if max_val >= best_match["val"]:
                loc = (x+max_loc[0], y+max_loc[1], img_tmpl.shape[1], img_tmpl.shape[0])
                best_match = {"name": tmpl.name, "loc": loc, "val": max_val}
            if max_val >= self.config["match_threshold"]:
                break
        log.info(f"Matched {best_match}")

        if show:
            display_image = screen.copy()
            loc = best_match["loc"]
            top_left = (loc[0], loc[1])
            bottom_right = (loc[0] + loc[2], loc[1] + loc[3])
            cv2.rectangle(display_image, top_left, bottom_right, (0, 0, 255), 3)
            cv2.imshow("match", display_image)
            cv2.waitKey(2000)
            cv2.destroyAllWindows()

        return Match(**best_match)