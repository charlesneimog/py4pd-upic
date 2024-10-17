import pd

try:
    from svgelements import *
    from svgpathtools import svg2paths

except Exception as e:
    pd.error("Error to load svg2data: " + str(e))


from .upic.svgItens import *


def py4pd_upic_setup():
    pd.add_object(playSvg, "playsvg", playable=True, py_out=True, ignore_none_return=True)

    # convertion

    # filters
    pd.add_object(svg_filter, "attrfilter", py_out=True, ignore_none_return=True)
    pd.add_object(svg_get, "attrget", py_out=False, ignore_none_return=True)

    # subevents
    pd.add_object(getsubevents, "getchilds", py_out=True, ignore_none_return=True)
    pd.add_object(playchilds, "playchilds", py_out=True, ignore_none_return=True, playable=True)

    # paths
    pd.add_object(getPath, "getpath", py_out=True, ignore_none_return=True)
    pd.add_object(playpath, "playpath", py_out=True, ignore_none_return=True, playable=True)

    # =
    pd.print("[upic] by Charles K. Neimog!", show_prefix=False)
