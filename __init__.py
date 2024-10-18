import pd

try:
    from svgelements import *
    from svgpathtools import svg2paths

except Exception as e:
    pd.error("Error to load svg2data: " + str(e))


from .upic.svgItens import *


def py4pd_upic_setup():
    random = pd.new_object("u.playsvg")
    random.addmethod("read", readSvg)
    random.playable = True
    random.py_out = True
    random.ignore_none = True
    random.add_object()
    # playpath = pd.new_object("u.playpath")
    # playpath.py_out = True
    # playpath.ignore_none_return = True
    # playpath.addmethod("read", readSvg)
    # playpath.addobject()

    # convertion

    # filters
    pd.add_object(svg_filter, "u.filterattr", py_out=True, ignore_none_return=True)
    pd.add_object(svg_get, "u.getattr", py_out=False, ignore_none_return=True)

    # subevents
    pd.add_object(getsubevents, "u.getchilds", py_out=True, ignore_none_return=True)
    pd.add_object(playchilds, "u.playchilds", py_out=True, ignore_none_return=True, playable=True)

    # paths
    pd.add_object(getPath, "u.getpath", py_out=True, ignore_none_return=True)
    pd.add_object(playpath, "u.playpath", py_out=True, ignore_none_return=True, playable=True)

    # =
    pd.print("[upic] by Charles K. Neimog (2024)", show_prefix=False)
