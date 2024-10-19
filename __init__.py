import pd

try:
    # from svgelements import *
    from svgpathtools import svg2paths

except Exception as e:
    pd.error("Error to load svg2data: " + str(e))


from .upic.svgItens import *


def py4pd_upic_setup():
    upic_play = pd.new_object("u.playsvg")
    upic_play.addmethod("read", readSvg)
    upic_play.playable = True
    upic_play.py_out = True
    upic_play.ignore_none = True
    upic_play.add_object()
    # convertion

    pd.add_object(readSvg, "u.playsvgt", py_out=True, ignore_none=True, playable=True)

    # filters
    pd.add_object(svg_filter, "u.filterattr", py_out=True, ignore_none=True)
    pd.add_object(svg_get, "u.getattr", py_out=False, ignore_none=True)

    # subevents
    pd.add_object(getsubevents, "u.getchilds", py_out=True, ignore_none=True)
    pd.add_object(playchilds, "u.playchilds", py_out=True, ignore_none=True, playable=True)

    # paths
    pd.add_object(buildPaths, "u.getpath", py_out=True, ignore_none=True)
    pd.add_object(playpath, "u.playpath", py_out=True, ignore_none=True, playable=True)
    # pd.add_object(playpathtest, "u.playpathtest", py_out=True, ignore_none=True, playable=True)

    # =
    pd.print("[upic] by Charles K. Neimog (2024)", show_prefix=False)
