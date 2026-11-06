#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
import struct
import inkex
from inkex.paths import Path as InkexPath
from inkex.transforms import Transform
from lxml import etree

# ------------------------------------------------------------
# CONFIG
# ------------------------------------------------------------

FONT_NAME        = "HersheyCustom"
UNITS_PER_EM     = 1000
ASCENT           = 800
DESCENT          = -200
SOURCE_FONT_SIZE = 10.0
SCALE            = UNITS_PER_EM / SOURCE_FONT_SIZE
HORIZ_ADV_X      = 500

SVG_NS = "http://www.w3.org/2000/svg"
INK_NS = "http://www.inkscape.org/namespaces/inkscape"

META = {
    "License": "SIL Open Font License http://scripts.sil.org/OFL",
    "Note":    "SIL OFL per metadata, Auto, by script made by Fomenal@free.fr",
}

# Hershey : plage de normalisation
TARGET_RANGE = 120

# ------------------------------------------------------------
# HELPERS
# ------------------------------------------------------------

def get_glyph_groups(root):
    return [e for e in root.iter() if e.get("id", "").startswith("glyph_U+")]

def get_metrics_map(root):
    return {
        e.get("id").replace("metrics_", "glyph_"): e
        for e in root.iter()
        if e.get("id", "").startswith("metrics_U+")
    }

def parse_translate(transform_str):
    if not transform_str:
        return 0.0, 0.0
    nums = re.findall(r"-?\d*\.?\d+", transform_str)
    if len(nums) >= 2:
        return float(nums[0]), float(nums[1])
    return 0.0, 0.0

def collect_paths(elem):
    tag = etree.QName(elem.tag).localname if "}" in elem.tag else elem.tag
    if tag == "path":
        d = elem.get("d", "").strip()
        return [d] if d else []
    d_parts = []
    for child in elem.iter():
        ctag = etree.QName(child.tag).localname if "}" in child.tag else child.tag
        if ctag == "path":
            d = child.get("d", "").strip()
            if d:
                d_parts.append(d)
    return d_parts

def hershey_normalize(v):
    v = round(v / UNITS_PER_EM * TARGET_RANGE)
    return max(-127, min(127, int(v)))

def parse_segments(d):
    segments = []
    last = None
    for seg in InkexPath(d).to_absolute():
        name = type(seg).__name__
        if name == "Move":
            last = (seg.arg1.real, seg.arg1.imag)
        elif name == "Line":
            pt = (seg.arg1.real, seg.arg1.imag)
            if last:
                segments.append((*last, *pt))
            last = pt
        elif name in ("Quadratic", "Curve"):
            # approximation : segment vers le point final
            pt = (seg.arg2.real, seg.arg2.imag)
            if last:
                segments.append((*last, *pt))
            last = pt
        elif name == "ZoneClose":
            last = None
    return segments

# ------------------------------------------------------------
# BUILD
# ------------------------------------------------------------

def build_font_svg(root, font_name, output_path, horiz_adv_x=500):
    glyph_groups = get_glyph_groups(root)
    metrics_map  = get_metrics_map(root)

    svg      = etree.Element("svg", xmlns=SVG_NS)
    metadata = etree.SubElement(svg, "metadata")
    metadata.text = "\n" + "".join(f"{k}: {v}\n" for k, v in META.items())
    defs = etree.SubElement(svg, "defs")
    font = etree.SubElement(defs, "font", {"id": font_name, "horiz-adv-x": str(horiz_adv_x)})

    etree.SubElement(font, "font-face", {
        "font-family":  font_name,
        "units-per-em": str(UNITS_PER_EM),
        "ascent":       str(ASCENT),
        "descent":      str(DESCENT),
    })
    etree.SubElement(font, "missing-glyph", {"horiz-adv-x": str(UNITS_PER_EM // 2)})
    etree.SubElement(font, "glyph", {"unicode": " ", "glyph-name": "space", "horiz-adv-x": "378"})

    hershey_glyphs = []  # données accumulées pour .bin et .py

    for g in glyph_groups:
        gid = g.get("id", "")
        m = re.search(r"U\+([0-9A-Fa-f]{4,})", gid)
        if not m:
            continue

        char     = chr(int(m.group(1), 16))
        mg       = metrics_map.get(gid)
        if mg is None:
            continue

        rect = next((e for e in mg.iter() if etree.QName(e.tag).localname == "rect"), None)
        if rect is None:
            continue

        rx  = float(rect.get("x", 0))
        ry  = float(rect.get("y", 0))
        rw  = float(rect.get("width",  10))
        rh  = float(rect.get("height", 10))
        tx, ty = parse_translate(mg.get("transform", ""))

        ox = tx + rx
        oy = ty + ry + rh

        transform = Transform((SCALE, 0, 0, -SCALE, -ox * SCALE, oy * SCALE))

        d_parts = collect_paths(g)
        if not d_parts:
            continue

        final_parts = [str(InkexPath(d).transform(transform)) for d in d_parts]
        d_out = " ".join(final_parts)
        adv   = int(rw * SCALE)

        etree.SubElement(font, "glyph", {
            "unicode":     char,
            "horiz-adv-x": str(adv),
            "d":           d_out,
        })

        # segments hershey depuis le d_out (espace fonte, M/L seulement)
        segments = []
        for part in final_parts:
            segments.extend(parse_segments(part))

        if segments:
            hershey_glyphs.append({
                "unicode":  ord(char),
                "advance":  max(1, int(round(adv / UNITS_PER_EM * TARGET_RANGE))),
                "segments": tuple(
                    (hershey_normalize(x1), hershey_normalize(y1),
                     hershey_normalize(x2), hershey_normalize(y2))
                    for x1, y1, x2, y2 in segments
                ),
            })

    # --- SVG ---
    etree.ElementTree(svg).write(str(output_path), encoding="utf-8", xml_declaration=True, pretty_print=True)

    # --- BIN ---
    bin_path = output_path.with_suffix(".bin")
    with open(bin_path, "wb") as f:
        f.write(struct.pack("<Hhh", len(hershey_glyphs), ASCENT, DESCENT))
        idx_pos = f.tell()
        for _ in hershey_glyphs:
            f.write(struct.pack("<HI", 0, 0))
        offsets = []
        for gh in hershey_glyphs:
            offsets.append(f.tell())
            f.write(struct.pack("<BB", gh["advance"], len(gh["segments"])))
            for s in gh["segments"]:
                f.write(struct.pack("<bbbb", *s))
        f.seek(idx_pos)
        for gh, off in zip(hershey_glyphs, offsets):
            f.write(struct.pack("<HI", gh["unicode"], off))

    # --- PY ---
    py_path = output_path.with_suffix(".py")
    with open(py_path, "w", encoding="utf-8") as f:
        f.write("# Auto-generated Hershey font (MicroPython compatible)\n\n")
        f.write(f"FONT_HEADER = {{'glyph_count': {len(hershey_glyphs)}, 'ascent': {ASCENT}, 'descent': {DESCENT}}}\n\n")
        f.write("GLYPH_INDEX = {\n")
        for i, gh in enumerate(hershey_glyphs):
            ch = chr(gh["unicode"])
            f.write(f"    0x{gh['unicode']:04X}: ({i}, {gh['advance']}, {len(gh['segments'])}),  # '{ch}'\n")
        f.write("}\n\nGLYPH_DATA = [\n")
        for gh in hershey_glyphs:
            f.write(f"    ({gh['advance']}, {gh['segments']}),\n")
        f.write("]\n")

    return len(glyph_groups), len(hershey_glyphs)

# ------------------------------------------------------------
# EXTENSION
# ------------------------------------------------------------

class ExportSVGFont(inkex.Effect):

    def add_arguments(self, pars):
        pars.add_argument("--font-name",    type=str, dest="font_name",    default="My_HersheyCustom")
        pars.add_argument("--output-file",  type=str, dest="output_path",  default="./")
        pars.add_argument("--units-per-em", type=int, dest="units_per_em", default=1000)
        pars.add_argument("--ascent",       type=int, dest="ascent",       default=800)
        pars.add_argument("--horiz-adv-x",  type=int, dest="horiz_adv_x",  default=500)
        pars.add_argument("--descent",      type=int, dest="descent",      default=-200)

    def effect(self):
        global FONT_NAME, UNITS_PER_EM, ASCENT, DESCENT, SCALE

        FONT_NAME    = self.options.font_name
        UNITS_PER_EM = self.options.units_per_em
        ASCENT       = self.options.ascent
        DESCENT      = self.options.descent
        SCALE        = UNITS_PER_EM / SOURCE_FONT_SIZE
        HORIZ_ADV_X  = self.options.horiz_adv_x

        from pathlib import Path
        output_fichier = Path(self.options.output_path) / (self.options.font_name + ".svg")
        try:
            n_svg, n_hershey = build_font_svg(self.document.getroot(), FONT_NAME, output_fichier, HORIZ_ADV_X)
            inkex.utils.debug(f"OK {n_svg} glyphes SVG, {n_hershey} glyphes Hershey -> {output_fichier.parent}")
        except Exception as e:
            import traceback
            inkex.utils.debug(f"ERREUR: {e}\n{traceback.format_exc()}")


if __name__ == "__main__":
    ExportSVGFont().run()
