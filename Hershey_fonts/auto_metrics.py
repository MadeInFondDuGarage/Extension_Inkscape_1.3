#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import inkex
from inkex.paths import Path as InkexPath
from lxml import etree

class AutoMetrics(inkex.Effect):

    def add_arguments(self, pars):
        pars.add_argument("--padding", type=float, dest="padding", default=0.5)

    def effect(self):
        root    = self.document.getroot()
        padding = self.options.padding

        glyphs  = {e.get("id"): e for e in root.iter() if e.get("id","").startswith("glyph_U+")}
        metrics = {e.get("id"): e for e in root.iter() if e.get("id","").startswith("metrics_U+")}

        updated = 0
        for gid, gelem in glyphs.items():
            mid  = gid.replace("glyph_", "metrics_")
            rect = metrics.get(mid)
            if rect is None:
                continue

            d = gelem.get("d", "").strip()
            if not d:
                continue

            bb = InkexPath(d).bounding_box()
            if bb is None:
                continue

            new_w = bb.width + padding * 2

            rect.set("width", f"{new_w:.4f}")
            updated += 1

        #inkex.utils.debug(f"✅ {updated} métriques mis à jour")


if __name__ == "__main__":
    AutoMetrics().run()
