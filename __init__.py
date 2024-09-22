import os
import sys

import pd

print = pd.print

try:
    import xml.dom.minidom

    from svgelements import *
    from svgpathtools import svg2paths

except Exception as e:
    pd.error("Error to load svg2data: " + str(e))



from .upic.svgItens import *


class ThingToPlay:
    def __init__(self):
        self.onset = 0
        self.color = ""
        self.duration = 0
        self.pitch = 0
        self.velocity = 0
        self.color = 0

    def __repr__(self) -> str:
        return "<Onset[" + str(self.onset) + "]>"


def py4pd_upic_setup():
    pd.add_object(
        readSvg, "readsvg", playable=True, py_out=True, ignore_none_return=True
    )
    pd.add_object(outputValues, "svg2pd")
    pd.add_object(svg_filter, "attrfilter", py_out=True, ignore_none_return=True)
    pd.add_object(svg_get, "getattr", py_out=False, ignore_none_return=True)

    # =
    pd.print("[upic] by Charles K. Neimog!", show_prefix=False)





