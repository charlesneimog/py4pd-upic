import os
from xml.dom.minidom import parse

import pd
from svgpathtools import svg2paths2

print = pd.print


class UPIC:
    def __init__(self):
        self.Systems = []
        self.Events = []
        self.viewBox = None

    def __repr__(self):
        return f"<Piece | {len(self.Events)} events>"


class System:
    def __init__(self):
        self.Id = ""
        self.startX = 0.0
        self.startY = 0.0
        self.width = 0.0
        self.height = 0.0
        self.properties = []
        self.start = 0.0
        self.duration = 0.0
        self.Events = []

    class Tokens:
        def __init__(self):
            self.tokens = []

        def __repr__(self):
            return f"<Tokens: {len(self.tokens)}>"

    def setProperties(self, values):
        values = values.split(",")
        for value in values:
            if value != "":
                localTokens = self.Tokens()
                tokens = value.split()
                localTokens.tokens = [item for item in tokens if item != ""]
                self.properties.append(localTokens)

    def getProperties(self):
        mytokens = []
        for prop in self.properties:
            mytokens.append(prop.tokens)
        return mytokens

    def processProperties(self):
        for prop in self.properties:
            if prop.tokens[0] == "duration":
                self.duration = float(prop.tokens[1])
            elif prop.tokens[0] == "start":
                self.start = float(prop.tokens[1])

    def __repr__(self):
        return f"<System: {self.duration}ms>"


class TextItem:
    def __init__(self):
        self.x = 0.0
        self.y = 0.0
        self.text = ""

    def __repr__(self):
        return f"<Text: ({self.x}, {self.y})>"


class SvgEvent:
    def __init__(self):
        self.x = 0.0
        self.y = 0.0
        self.id = ""
        self.width = 0.0
        self.heigh = 0.0
        self.rangeUp = 0.0
        self.rangeDown = 0.0
        self.verticalPosition = 0.0
        self.pathPattern = ""
        self.finalPoints = []
        self.countId = 0
        self.pathPoints = []
        self.color = ""
        self.sides = 0
        self.type = ""

    def setPathColor(self, attr):
        color = attr["style"].split(";")
        color = [
            item.split(":")[1] for item in color if "stroke" == item.split(":")[0]
        ][0]
        self.color = color

    def getPathPattern(self, attr):
        keys = attr["style"].split(";")
        strokeWidth = None
        strokeDasharray = None

        thereIsNoStroke = True
        for key in keys:
            if "stroke-dasharray" in key:
                thereIsNoStroke = False

        if thereIsNoStroke:
            self.pathPattern = "default" 
            return


        strokeWidth = float(
            [
                item.split(":")[1]
                for item in keys
                if "stroke-width" == item.split(":")[0]
            ][0]
        )
        # pd.print(keys)
        strokeDasharray = [
            item.split(":")[1]
            for item in keys
            if "stroke-dasharray" == item.split(":")[0]
        ][0].split(",")
        try:
            strokeDasharray = [
                round(float(item) / strokeWidth) for item in strokeDasharray
            ]
            strokeDasharray = "P" + "".join([str(item) for item in strokeDasharray])
            self.pathPattern = strokeDasharray
        except:
            self.pathPattern = "default"

    def setColor(self, attr):
        color = attr["style"].split(";")
        color = [item.split(":")[1] for item in color if "fill" == item.split(":")[0]][
            0
        ]
        self.color = color

    def __repr__(self):
        if "Polygon" in self.type:
            return f"<Polygon_{self.sides}: ({round(self.x, 2)}, {round(self.y, 2)})>"
        elif "Path" in self.type:
            return f"<Path: {len(self.pathPoints)} points>"
        elif "Rect" in self.type:
            return f"<Rect: ({self.x}, {self.y})>"
        elif "Ellipse" in self.type:
            return f"<Ellipse: ({self.x}, {self.y})>"
        elif "Star" in self.type:
            return f"<Star: ({self.x}, {self.y})>"
        else:
            return f"<Not Implemented Event: ({self.x}, {self.y})>"



def getElementHtml(parsed_svg, elem_str, id):
    elems = parsed_svg.getElementsByTagName(elem_str)
    alreadySet = False
    foundedElem = None
    for elem in elems:
        if elem.getAttribute("id") == id and not alreadySet:
            foundedElem = elem
            alreadySet = True
    return foundedElem



def getSvg(svg_file):
    """
    This get the data of svg and put in on time. I split the properties in two things.
    What we call "routers" and what we call "parameters".
    Rourters are:
        - Path Pattern
        - Color

    Parameters are:
        - Vertical Position
        - Horizontal Position (Tempo)
        - Width (not yet)

    """
    home = pd.get_patch_dir()
    svg_file = os.path.join(home, svg_file)
    parsed_svg = parse(svg_file)
    try:
        paths, attributes, svg_attributes = svg2paths2(svg_file)
    except:
        pd.error("Error parsing SVG")
        return

    UpicPiece = UPIC()
    UpicPiece.viewBox = svg_attributes["viewBox"]
    pathCount = 0
    ellipseCount = 0
    rectCount = 0
    Events = []
    Systems = []
    for path, attr in zip(paths, attributes):
        event = SvgEvent()
        if "sodipodi:type" in attr:
            if "sodipodi:sides" in attr:
                cx = float(attr["sodipodi:cx"])
                cy = float(attr["sodipodi:cy"])
                event.x = cx
                event.y = cy
                event.id = attr["id"]
                event.color = attr["style"].split(";")[0].split(":")[1]
                if "inkscape:flatsided" in attr:
                    isNotStar = attr["inkscape:flatsided"]
                    if isNotStar == "true":
                        event.type = "Polygon"
                    else:
                        event.type = "Star"
                event.sides = int(attr["sodipodi:sides"])
                Events.append(event)
            else:
                pd.error("Polygon without sides, this is not supported yet")
                return None
        else:
            style = attr["style"]
            attrId = attr["id"]
            if "fill:none" in style and "rect" in attrId:
                timeSystem = System()
                timeSystem.startX = float(attr["x"])
                timeSystem.startY = float(attr["y"])
                timeSystem.width = float(attr["width"])
                timeSystem.height = float(attr["height"])
                rectID = attr["id"]
                rects = parsed_svg.getElementsByTagName("rect")
                alreadySet = False
                for rect in rects:
                    if rect.getAttribute("id") == rectID and not alreadySet:
                        descInsideRect = rect.getElementsByTagName("desc")
                        if len(descInsideRect) == 0:
                            pd.error(
                                "No description inside rect, you must at least set the duration!"
                            )
                            Systems.append(timeSystem)
                            alreadySet = True
                            continue
                        desc_content = descInsideRect[0].firstChild.nodeValue.strip()
                        timeSystem.setProperties(desc_content)
                        timeSystem.processProperties()
                        Systems.append(timeSystem)
                        alreadySet = True
                    elif rect.getAttribute("id") == rectID and alreadySet:
                        pd.error("System already set")

            elif "path" in attrId:
                if "d" in attr:
                    elem = getElementHtml(parsed_svg, "path", attrId)
                    if elem is not None:
                        desc = elem.getElementsByTagName("desc")
                        if len(desc) != 0:
                            if len(desc) > 1:
                                raise ValueError("Only one description is allowed")
                            descContent = desc[0].firstChild.nodeValue.strip()
                            descMessages = descContent.split(";")
                            descMessages = [item for item in descMessages if item != ""]

                    event.type = "Path"
                    event.countId = pathCount
                    event.id = attrId
                    pathCount += 1
                    event.setPathColor(attr)
                    event.getPathPattern(attr)
                    xPointBefore = 0
                    for x in path:
                        if x.start.real < xPointBefore:
                            raise ValueError(
                                "We use x values for time, we can't go back in time yet!!"
                            )
                        xPointBefore = x.start.real
                    event.pathPoints = path
                    event.x = path[0].start.real
                    event.y = path[0].start.imag
                    Events.append(event)
                    continue
                else:
                    event.type = "Ellipse"
                    event.countId = ellipseCount
                    event.id = attrId
                    ellipseCount += 1
                    event.x = float(attr["cx"])
                    event.y = float(attr["cy"])
                    event.width = float(attr["rx"]) * 2
                    event.setColor(attr)
                    Events.append(event)
                    continue
            elif "rect" in attrId:
                event.type = "Rect"
                event.countId = rectCount
                event.id = attrId
                rectCount += 1
                event.x = float(attr["x"])
                event.y = float(attr["y"])
                event.width = float(attr["width"])
                event.heigh = float(attr["height"])
                Events.append(event)
                continue
            else:
                pd.error("Event not recognized, {}".format(attrId))

    UpicPiece.Events = Events
    UpicPiece.Systems = Systems
    return UpicPiece


def cubicBezier(start, control1, control2, end, num_points=100):
    points = []
    for t in range(num_points + 1):
        t /= num_points
        x = (
            (1 - t) ** 3 * start.real
            + 3 * (1 - t) ** 2 * t * control1.real
            + 3 * (1 - t) * t**2 * control2.real
            + t**3 * end.real
        )
        y = (
            (1 - t) ** 3 * start.imag
            + 3 * (1 - t) ** 2 * t * control1.imag
            + 3 * (1 - t) * t**2 * control2.imag
            + t**3 * end.imag
        )
        points.append((x, y))
    return points


def getOnset(system, point):
    horizontalSpan = system.width - system.startX
    firstPoint = point - system.startX
    return int(firstPoint * system.duration / horizontalSpan)


# X is horizontal position
# Y is vertical position
def getPathCompleteLine(system, event, points):
    msOnsetInitial = getOnset(system, points[0].start.real)
    msOnsetFinal = getOnset(system, points[-1].end.real)
    lengthInMs = msOnsetFinal - msOnsetInitial
    finalX_Y_Points = []
    onset = -1
    stepForBlock = 1000 / pd.get_sample_rate() * pd.get_vec_size() * 4 # step
    for point in points:
        className = getattr(point, "__class__")
        if className.__name__ == "CubicBezier":
            cubicBezierPoints = cubicBezier(
                point.start, point.control1, point.control2, point.end, lengthInMs
            )
            for cubicBezierPoint in cubicBezierPoints:
                thisOnset = getOnset(system, cubicBezierPoint[0])
                if thisOnset != onset:
                    finalX_Y_Points.append(cubicBezierPoint)
                    onset = thisOnset
        else:
            raise ValueError("Only CubicBezier supported for now")

    previousOnset = msOnsetInitial - stepForBlock
    for point in finalX_Y_Points:
        onsetPoint = getOnset(system, point[0])
        if onsetPoint > previousOnset + stepForBlock + 1:
            bezierEvent = SvgEvent()
            bezierEvent.type = "Path"
            bezierEvent.id = event.id
            bezierEvent.color = event.color
            bezierEvent.countId = event.countId
            bezierEvent.finalPoints = point
            bezierEvent.pathPattern = event.pathPattern
            verticalProportinalPosicion = system.height - (point[1] - system.startY)
            bezierEvent.verticalPosition = verticalProportinalPosicion / system.height
            pd.add_to_player(onsetPoint, bezierEvent)
            previousOnset = onsetPoint


def readSvg(svg_file):
    UpicPiece = getSvg(svg_file)
    if UpicPiece is None:
        return None
    pd.clear_player()

    # Systems as Score Systems (here retangles)
    for system in UpicPiece.Systems:
        width = system.width
        height = system.height
        startX = system.startX
        startY = system.startY
        finishX = startX + width
        finishY = startY + height
        for event in UpicPiece.Events:
            if (
                event.x > startX
                and event.x < finishX
                and event.y > startY
                and event.y < finishY
                and event.type != "Path"
            ):
                horizontalSpan = system.width - system.startX
                verticalProportinalPosicion = system.height - (event.y - system.startY)
                duration = event.width * system.duration / system.width
                event.duration = duration
                event.verticalPosition = verticalProportinalPosicion / system.height
                onset = int(
                    (event.x - system.startX) * system.duration / horizontalSpan
                )
                onset = system.start + onset
                pd.add_to_player(onset, event)


            elif event.type == "Path":
                points = []
                inside = True
                for path in event.pathPoints:
                    if (
                        path.start.real > startX
                        and path.start.real < finishX
                        and path.start.imag > startY
                        and path.start.imag < finishY
                    ):
                        points.append(path)
                    else:
                        inside = False
                if inside:
                    getPathCompleteLine(system, event, points)

            elif event.type == "Polygon":
                pd.print("Ellipse not supported yet")
                pass

            elif event.type == "Star":
                pd.print("Star not supported yet")
                pass

    print("Done!")

def svg_filter(event, attr, value):
    if hasattr(event, attr):
        eventValue = getattr(event, attr)
        if eventValue == value:
            return event
        else:
            return None
    else: 
        return None

def svg_get(event, attr):

    if hasattr(event, attr):
        eventValue = getattr(event, attr)
        return eventValue
    else: 
        return None


def outputValues(event):
    # always using type, id, color, 
    if event.type in ["Ellipse", "Star", "Polygon"]:
        pd.out(
            [
                event.type, 
                event.id, 
                event.color, 
                event.countId, 
                event.verticalPosition, 
                event.duration
            ]
        )


    elif event.type == "Path":
        pd.out(
            [
                event.type,
                event.id,
                event.color,
                event.pathPattern,
                event.countId,
                event.verticalPosition,
            ]
        )


