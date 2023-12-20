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
        strokeWidth = float(
            [
                item.split(":")[1]
                for item in keys
                if "stroke-width" == item.split(":")[0]
            ][0]
        )
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
            self.pathPattern = None

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
        else:
            return f"<Event: ({self.x}, {self.y})>"


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
    paths, attributes, svg_attributes = svg2paths2(svg_file)
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
                event.color = attr["style"].split(";")[0].split(":")[1]
                event.sides = int(attr["sodipodi:sides"])
                event.type = "Polygon"
                Events.append(event)
            else:
                pd.error("Polygon without sides, this is not supported yet")
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
                    event.type = "Path"
                    event.countId = pathCount
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
                    ellipseCount += 1
                    event.x = float(attr["cx"])
                    event.y = float(attr["cy"])
                    event.setColor(attr)
                    Events.append(event)
                    continue
            elif "rect" in attrId:
                event.type = "Rect"
                event.countId = rectCount
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
    for point in finalX_Y_Points:
        bezierEvent = SvgEvent()
        bezierEvent.type = "Path"
        bezierEvent.color = event.color
        bezierEvent.countId = event.countId
        bezierEvent.finalPoints = point
        bezierEvent.pathPattern = event.pathPattern
        verticalProportinalPosicion = system.height - (point[1] - system.startY)
        bezierEvent.verticalPosition = verticalProportinalPosicion / system.height
        onsetPoint = getOnset(system, point[0])
        pd.add_to_player(onsetPoint, bezierEvent)


def readSvg(svg_file):
    UpicPiece = getSvg(svg_file)
    pd.clear_player()
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
                        # TODO: Add warning if not inside any system
                        inside = False
                        pass
                if inside:
                    getPathCompleteLine(system, event, points)
    print("Done!")


def outputValues(event):
    if event.type == "Ellipse":
        pd.out([event.type, event.color, event.countId, event.verticalPosition])

    elif event.type == "Path":
        pd.out(
            [
                event.type,
                event.color,
                event.pathPattern,
                event.countId,
                event.verticalPosition,
            ]
        )
