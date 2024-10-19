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
        self.pathSystem = None
        self.points = []

    def __repr__(self):
        return f"<Piece | {len(self.Events)} events>"


class System:
    def __init__(self):
        self.Id = ""
        self.x = 0.0
        self.y = 0.0
        self.width = 0.0
        self.height = 0.0
        self.properties = []
        self.onset = 0.0
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
                self.onset = float(prop.tokens[1])

    def __repr__(self):
        return f"<System: {self.duration}ms>"


class SvgEvent:
    def __init__(self):
        self.x = 0.0
        self.y = 0.0
        self.count = 0
        self.id = ""
        self.width = 0.0
        self.height = 0.0
        self.verticalPosition = 0.0
        self.finalPoints = []
        self.points = []
        self.system: System
        self.color = ""
        self.fill = ""
        self.stroke = ""
        self.sides = 0
        self.eventType = ""
        self.notTemporal = False
        self.properties = []

        self.first = False
        self.last = False

        self.duration = 0
        self.onset = 0

        # subevents
        self.childs = []
        self.father: SvgEvent

    def setStrokeColor(self, attr):
        try:
            color = attr["style"].split(";")
            color = [item.split(":")[1] for item in color if "stroke" == item.split(":")[0]][0]
            self.stroke = color
        except:
            self.stroke = ""

    def setFillColor(self, attr):
        try:
            color = attr["style"].split(";")
            color = [item.split(":")[1] for item in color if "fill" == item.split(":")[0]][0]
            self.fill = color
        except:
            self.fill = ""

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

        strokeWidth = float([item.split(":")[1] for item in keys if "stroke-width" == item.split(":")[0]][0])
        # pd.print(keys)
        strokeDasharray = [item.split(":")[1] for item in keys if "stroke-dasharray" == item.split(":")[0]][0].split(",")
        try:
            strokeDasharray = [round(float(item) / strokeWidth) for item in strokeDasharray]
            strokeDasharray = "P" + "".join([str(item) for item in strokeDasharray])
            self.pathPattern = strokeDasharray
        except:
            self.pathPattern = "default"

    def __repr__(self):
        if "Polygon" in self.eventType:
            return f"<Polygon_{self.sides}: ({round(self.x, 2)}, {round(self.y, 2)})>"
        elif "Path" in self.eventType:
            return f"<Path: {len(self.points)} points>"
        elif "Rect" in self.eventType:
            return f"<Rect: ({self.x}, {self.y})>"
        elif "Ellipse" in self.eventType:
            return f"<Ellipse: ({self.x}, {self.y})>"
        elif "Star" in self.eventType:
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


def getEventProperties(elem) -> list:
    if elem is None:
        return []
    desc = elem.getElementsByTagName("desc")
    properties = []
    if len(desc) != 0:
        if len(desc) > 1:
            raise ValueError("Only one description is allowed")
        descContent = desc[0].firstChild.nodeValue.strip()
        descMessages = descContent.split(",")
        descMessages = [item for item in descMessages if item != ""]
        properties = descMessages

    formatedProperties = []
    for prop in properties:
        tokens = prop.split()
        formatedProperties.append(tokens)

    return properties


def getSystems(parsed_svg, attr):
    timeSystem = System()
    timeSystem.x = float(attr["x"])
    timeSystem.y = float(attr["y"])
    timeSystem.width = float(attr["width"])
    timeSystem.height = float(attr["height"])
    rectID = attr["id"]

    rects = parsed_svg.getElementsByTagName("rect")
    alreadySet = False
    newsystems = []
    for rect in rects:
        if rect.getAttribute("id") == rectID and not alreadySet:
            descInsideRect = rect.getElementsByTagName("desc")
            if len(descInsideRect) == 0:
                raise Exception("No description inside rect, you must at least set the duration!")
            desc_content = descInsideRect[0].firstChild.nodeValue.strip()
            timeSystem.setProperties(desc_content)
            timeSystem.processProperties()
            newsystems.append(timeSystem)
            alreadySet = True
        elif rect.getAttribute("id") == rectID and alreadySet:
            raise ValueError("System already set")
    return newsystems


def getSvg(svg_file: str) -> UPIC:
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
        things = svg2paths2(svg_file)
        if len(things) == 3:
            paths, attributes, svg_attributes = things
        else:
            raise ValueError("We need 3 things, paths, attributes and svg_attributes")
    except:
        raise ValueError("Error parsing SVG file")

    piece: UPIC = UPIC()
    piece.viewBox = svg_attributes["viewBox"]
    events: list[SvgEvent] = []
    systems: list[System] = []
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
                        event.eventType = "Polygon"
                    else:
                        event.eventType = "Star"
                event.sides = int(attr["sodipodi:sides"])
                events.append(event)
            else:
                raise Exception("Polygon without sides, this is not supported yet")
        else:
            style = attr["style"]
            attrId = attr["id"]

            # System
            if "fill:none" in style and "stroke:#000000" in style and "rect" in attrId:
                newsystems = getSystems(parsed_svg, attr)
                for system in newsystems:
                    systems.append(system)

            # Music Events
            elif "path" in attrId:
                if "d" in attr:
                    event.eventType = "Path"
                    event.id = attrId
                    event.setStrokeColor(attr)
                    event.getPathPattern(attr)
                    xPointBefore = 0
                    for x in path:
                        if x.start.real < xPointBefore:
                            event.notTemporal = True
                        xPointBefore = x.start.real
                    event.points = path
                    event.x = path[0].start.real
                    event.y = path[0].start.imag
                    elem = getElementHtml(parsed_svg, "path", attrId)
                    event.properties = getEventProperties(elem)
                    events.append(event)
                    continue
                else:
                    event.eventType = "Ellipse"
                    event.id = attrId
                    elem = getElementHtml(parsed_svg, "ellipse", attrId)
                    event.properties = getEventProperties(elem)
                    event.x = float(attr["cx"])
                    event.y = float(attr["cy"])

                    if "r" in attr:
                        event.height = float(attr["r"]) * 2
                        event.width = float(attr["r"]) * 2
                    else:
                        event.height = float(attr["ry"]) * 2
                        event.width = float(attr["rx"]) * 2

                    event.setFillColor(attr)
                    event.setStrokeColor(attr)
                    events.append(event)
                    continue
            elif "rect" in attrId:
                event.eventType = "Rect"
                event.id = attrId
                event.x = float(attr["x"])
                event.y = float(attr["y"])
                event.width = float(attr["width"])
                event.height = float(attr["height"])
                event.setFillColor(attr)
                event.setStrokeColor(attr)
                elem = getElementHtml(parsed_svg, "rect", attrId)
                event.properties = getEventProperties(elem)
                events.append(event)
                continue
            else:
                pd.error("Event not recognized, {}".format(attrId))

    piece.Events = events
    piece.Systems = systems
    return piece


def cubicBezier(start: float, control1: float, control2: float, end: float, num_points=100):
    points = []
    for t in range(num_points + 1):
        t /= num_points
        x = (1 - t) ** 3 * start.real + 3 * (1 - t) ** 2 * t * control1.real + 3 * (1 - t) * t**2 * control2.real + t**3 * end.real
        y = (1 - t) ** 3 * start.imag + 3 * (1 - t) ** 2 * t * control1.imag + 3 * (1 - t) * t**2 * control2.imag + t**3 * end.imag
        points.append((x, y))
    return points


def getOnset(system, point):
    horizontalSpan = system.width - system.x
    firstPoint = point - system.x
    return int(firstPoint * system.duration / horizontalSpan)


def buildPaths(event: SvgEvent):
    system = event.system
    points = event.points

    hasFather = event.father is not None
    if event.father is not None:
        system = event.father

    msOnsetInitial = getOnset(system, points[0].start.real)
    msOnsetFinal = getOnset(system, points[-1].end.real)
    lengthInMs = msOnsetFinal - msOnsetInitial

    finalX_Y_Points = []
    onset = -1
    stepForBlock = 1000 / pd.get_sample_rate() * pd.get_vec_size() * 4
    for point in points:
        className = getattr(point, "__class__")
        if className.__name__ == "CubicBezier":
            cubicBezierPoints = cubicBezier(point.start, point.control1, point.control2, point.end, lengthInMs)
            for cubicBezierPoint in cubicBezierPoints:
                thisOnset = getOnset(system, cubicBezierPoint[0])
                if thisOnset != onset:
                    finalX_Y_Points.append(cubicBezierPoint)
                    onset = thisOnset
        else:
            raise ValueError("Only CubicBezier supported for now")

    fatherHeight = system.height
    fatherY = system.y
    hasFather = event.father is not None
    if hasFather:
        fatherHeight = event.father.height
        fatherY = event.father.y

    points = []

    # rethink
    positionI = 0
    firstEvent = True

    lastEvent = finalX_Y_Points[-1]
    isLast = False

    for point in finalX_Y_Points:
        onset = getOnset(system, point[0])
        if point == lastEvent:
            isLast = True
        if onset > stepForBlock + 1:
            pathPoint = SvgEvent()
            if firstEvent:
                pathPoint.first = True
                firstEvent = False
            if isLast:
                pathPoint.last = True
            pathPoint.eventType = "Path"
            pathPoint.id = event.id
            pathPoint.stroke = event.stroke
            pathPoint.fill = event.fill
            pathPoint.count = positionI
            pathPoint.finalPoints = point
            pathPoint.pathPattern = event.pathPattern
            pathPoint.onset = onset
            vPos = fatherHeight - (point[1] - fatherY)
            pathPoint.verticalPosition = vPos / fatherHeight
            points.append(pathPoint)
            positionI += 1
    return points


def checkInsideElem(mainEvent: SvgEvent, subEvents: list[SvgEvent]):
    startX = mainEvent.x
    startY = mainEvent.y
    mainWidth = mainEvent.width
    mainHeight = mainEvent.height
    goodSubEvents = []
    for subEvent in subEvents:
        if subEvent == mainEvent:
            continue
        finishX = startX + mainWidth
        finishY = startY + mainHeight
        if subEvent.x > startX and subEvent.x < finishX and subEvent.y > startY and subEvent.y < finishY and subEvent.eventType != "Path":
            subEvent.father = mainEvent
            goodSubEvents.append(subEvent)
        elif subEvent.eventType == "Path":
            points = []
            inside = True
            for path in subEvent.points:
                if path.start.real > startX and path.start.real < finishX and path.start.imag > startY and path.start.imag < finishY:
                    points.append(path)
                else:
                    inside = False
            if inside:
                subEvent.father = mainEvent
                goodSubEvents.append(subEvent)
    return goodSubEvents


def readSvg(svg_file: str):
    piece = getSvg(svg_file)
    if piece is None:
        return None
    pd.clear_player()

    # Systems as Score Systems (here retangles)
    mainEvents = []
    for system in piece.Systems:
        width = system.width
        height = system.height
        startX = system.x
        startY = system.y
        finishX = startX + width
        finishY = startY + height
        for event in piece.Events:
            inside = event.x > startX and event.x < finishX and event.y > startY and event.y < finishY
            normalEvent = event.eventType in ["Ellipse", "Rect"]
            if inside and normalEvent:
                horizontalSpan = system.width - system.x
                verticalPos = system.height - (event.y - system.y)
                duration = event.width * system.duration / system.width
                event.duration = duration
                event.verticalPosition = verticalPos / system.height
                onset = int((event.x - system.x) * system.duration / horizontalSpan)
                onset = system.onset + onset
                event.System = system
                event.onset = onset
                event.childs = checkInsideElem(event, piece.Events)
                mainEvents.append(event)

            # star, polygons and others are paths
            if event.eventType == "Path":
                points = []
                inside = True

                for path in event.points:
                    if path.start.real > startX and path.start.real < finishX and path.start.imag > startY and path.start.imag < finishY:
                        points.append(path)
                    else:
                        inside = False
                        break
                if inside:
                    firstPointX = event.points[0].start.real
                    lastPointX = event.points[-1].end.real
                    event.width = lastPointX - firstPointX

                    horizontalSpan = system.width - system.x
                    duration = event.width * system.duration / system.width

                    event.duration = duration
                    onset = (firstPointX - system.x) * system.duration / horizontalSpan

                    onset = system.onset + onset
                    event.system = system
                    event.onset = onset
                    event.points = points
                    mainEvents.append(event)

            elif event.eventType == "Star" or event.eventType == "Polygon":
                raise Exception("Not implemented yet")
                points = []
                inside = True
                for path in event.points:
                    if path.start.real > x and path.start.real < finishX and path.start.imag > startY and path.start.imag < finishY:
                        points.append(path)
                    else:
                        inside = False
                        break
                if inside:
                    horizontalSpan = system.width - system.x
                    verticalPos = system.height - (event.y - system.y)
                    duration = event.width * system.duration / system.width
                    event.duration = duration
                    event.verticalPosition = verticalPos / system.height
                    onset = int((event.x - system.x) * system.duration / horizontalSpan)
                    onset = system.start + onset
                    event.System = system
                    event.onset = onset
                    event.childs = checkInsideElem(event, piece.Events)
                    mainEvents.append(event)

    if len(mainEvents) == 0:
        raise ValueError("No events found")

    firstonset = 0
    firstevent: SvgEvent = mainEvents[0]
    lastonset = 0
    lastevent: SvgEvent = mainEvents[0]

    for eventA in mainEvents:
        eventIsInsideOther = False
        for eventB in mainEvents:
            if eventB.eventType == "Path":
                continue
            if eventA in eventB.childs:
                eventIsInsideOther = True
                continue
        if not eventIsInsideOther:
            onset = eventA.onset

            # just to know first and last event
            if onset > lastonset:
                lastonset = onset
                lastevent = eventA
            if onset < firstonset:
                firstonset = onset
                firstevent = eventA

            pd.add_to_player(onset, eventA)

    lastevent.last = True
    firstevent.first = True

    print("Score loaded")


def playpath(events):
    pd.clear_player()
    if type(events) == SvgEvent:
        events = [events]

    for event in events:
        points = buildPaths(event)
        hasFather = event.father is not None
        point = points[0]
        for point in points:
            if hasFather:
                pd.add_to_player(point.onset, point)
            else:
                pd.add_to_player(point.onset, point)


def playchilds(event: list[SvgEvent]):
    pd.clear_player()
    fatherOnset = event[0].father
    for child in event:
        child_onset = child.onset - fatherOnset.onset
        pd.add_to_player(child_onset, child)


def svg_filter(events, attr: str, value):
    # check if event is a list
    if type(events) == list:
        passEvents = []
        for event in events:
            if hasattr(event, attr):
                eventValue = getattr(event, attr)
                if eventValue == value:
                    passEvents.append(event)

        if len(passEvents) != 0:
            return passEvents
        else:
            return
    elif type(events) == SvgEvent:
        event = events
        if hasattr(event, attr):
            eventValue = getattr(event, attr)
            if eventValue == value:
                return event
            else:
                return None
        else:
            return None
    else:
        raise Exception("u.filterattr: events must be a list or a SvgEvent")


def svg_get(event: SvgEvent, attr: str):
    if hasattr(event, attr):
        eventValue = getattr(event, attr)
        return eventValue
    else:
        raise Exception("Attribute not found")


def getsubevents(event: SvgEvent):
    if hasattr(event, "childs"):
        return event.childs


def outputValues(event: SvgEvent):
    # always using type, id, color,
    if event.eventType in ["Ellipse", "Star", "Polygon"]:
        pd.out(
            [
                event.eventType,
                event.id,
                event.fill,
                event.verticalPosition,
                event.duration,
            ]
        )

    elif event.eventType == "Path":
        pd.out(
            [
                event.eventType,
                event.id,
                event.stroke,
                event.pathPattern,
                event.verticalPosition,
            ]
        )
