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
    sys.exit()


from upic.svgItens import *


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


def svg2Data(svg_path, all_rects):
    """
    svg2Data take a svg file (always relative) and read the rect names. It return a List of onsets and midicents
    """
    pd.clear_player()

    start = 0
    scriptFileFolder = pd.get_patch_dir()
    svg_path = os.path.join(scriptFileFolder, svg_path)
    paths, attributes = svg2paths(svg_path)
    doc = xml.dom.minidom.parse(svg_path)

    text = [text.getAttribute("id") for text in doc.getElementsByTagName("text")]

    # get coordinates of the text
    text_x_coord = [text.getAttribute("x") for text in doc.getElementsByTagName("text")]
    text_y_coord = [text.getAttribute("y") for text in doc.getElementsByTagName("text")]

    # get content of the text
    text_content = [text.firstChild for text in doc.getElementsByTagName("text")]

    final_list = []

    for i in range(len(text)):
        try:
            scorexml = text_content[i].toxml()
            scorexml = bs4.BeautifulSoup(scorexml, "lxml")
            if scorexml.text == "":
                continue
            else:
                final_list.append(
                    [text[i], text_x_coord[i], text_y_coord[i], scorexml.text]
                )
        except BaseException:
            # print('Error in line 41')
            pass

    midicent_list = []
    # onset_list = []
    color_list = []
    id_list = []

    added_elements = []

    for path, attr in zip(paths, attributes):
        rectangleCoordantes = path.bbox()

        if attr["id"] in all_rects:
            texts_inside = []
            for i in range(len(final_list)):
                x_axis = float(final_list[i][1])
                y_axis = float(final_list[i][2])
                if (
                    x_axis > rectangleCoordantes[0]
                    and x_axis < rectangleCoordantes[1]
                    and y_axis > rectangleCoordantes[2]
                    and y_axis < rectangleCoordantes[3]
                ):
                    texts_inside.append(final_list[i][3])

            for text in texts_inside:
                text = text.replace("ms", "")
                try:  # DOC: This try to search for parameters inside the rect and add it.
                    text = text.replace("ms", "")
                    if "Duration" in text:
                        text = text.split("=")[1]
                        duration = eval(text)
                    elif "Pitches" in text:
                        pitch = text
                        text = text.split("=")[1]
                        pitch = eval(text)
                    elif "Start" in text:
                        text = text.split("=")[1]
                        start = eval(text)
                    elif "Channels" in text:
                        text = text.split("=")[1]
                    elif "Velocity" in text:
                        text = text.split("=")[1]

                # DOC: If there is no parameters inside the rect, it will use
                # the default values.
                except BaseException:
                    print("Error")
                    pass

            for path_inside, attr_inside in zip(paths, attributes):
                # get all paths inside the rectangle
                inside_coordantes = path_inside.bbox()

                # see if element is inside the rectangle
                left = (
                    rectangleCoordantes[0] < inside_coordantes[0],
                    rectangleCoordantes[0],
                    inside_coordantes[0],
                )  # left
                right = (
                    rectangleCoordantes[1] > inside_coordantes[1],
                    rectangleCoordantes[1],
                    inside_coordantes[1],
                )  # right
                top = (
                    rectangleCoordantes[2] < inside_coordantes[2],
                    rectangleCoordantes[2],
                    inside_coordantes[2],
                )  # top
                bottom = (
                    rectangleCoordantes[3] > inside_coordantes[3],
                    rectangleCoordantes[3],
                    inside_coordantes[3],
                )  # bottom

                # see if id of the element is in the list of text
                not_text = True
                if attr_inside["id"] in [i[0] for i in final_list]:
                    not_text = False
                try:
                    if left[0] and right[0] and top[0] and bottom[0] and not_text:
                        try:
                            color = attr_inside["style"]
                            color = color.split(";")
                            fill = [i for i in color if i.startswith("fill:")][0]
                            color = fill.split(":")[1]
                        except BaseException:
                            color = attr_inside["style"]
                            color = "#ffffff"
                            print("error to get color")

                        id_atribute = attr_inside["id"]
                        # if element is already in the dict, stop the loop
                        if id_atribute in added_elements:
                            break
                        # DOC: Set the MIDICENT value
                        added_elements.append(id_atribute)
                        midicent = (top[2] + bottom[2]) / 2
                        pitch_min = rectangleCoordantes[2]
                        pitch_max = rectangleCoordantes[3]
                        midicent = int(
                            om_scale(
                                midicent, pitch[0], pitch[1], pitch_min, pitch_max
                            )[0]
                        )
                        # the number is inverted, so we need to invert it
                        midicent = midicent - pitch[0]
                        midicent = pitch[1] - midicent
                        midicent_list.append(midicent)
                        color_list.append(color)

                        # DOC: Get the ONSET of the element
                        time = left[2]
                        time_min = rectangleCoordantes[0]
                        time_max = rectangleCoordantes[1]
                        time = int(om_scale(time, 0, duration, time_min, time_max)[0])
                        final_onset = time + start
                        thing = ThingToPlay()
                        thing.onset = final_onset
                        thing.pitch = midicent
                        thing.color = color
                        pd.add_to_player(final_onset, thing)

                        # DOC: Save the Id of the element
                        element_id = attr_inside["id"]
                        id_list.append(element_id)
                    else:
                        pass

                except BaseException:
                    print("Error")
                    pass

        else:
            pass
    pd.print("svg imported!")


def thing2pd(obj):
    list = [obj.pitch, obj.color, obj.onset]
    return list


def color2par(color):
    if color == "#0000ff":
        return "sound1"
    elif color == "#ffff00":
        return "sound2"
    elif color == "#008000":
        return "sound3"
    elif color == "#ff0000":
        return "sound4"


def py4pd_upic_setup():
    pd.add_object(
        readSvg, "readsvg", playable=True, pyout=True, ignore_none_return=True
    )
    pd.add_object(outputValues, "svg2pd")
