def get_tl_line_values(
    line,
    LTRB=True,
    withTranscription=False,
    withConfidence=False,
    imWidth=0,
    imHeight=0,
):
    """
    Validate the format of the line. If the line is not valid an exception will be raised.
    If maxWidth and maxHeight are specified, all points must be inside the image bounds.
    Possible values are:
    LTRB=True: xmin,ymin,xmax,ymax[,confidence][,transcription]
    LTRB=False: x1,y1,x2,y2,x3,y3,x4,y4[,confidence][,transcription]
    Returns values from a textline. Points , [Confidences], [Transcriptions]
    """
    confidence = 0.0
    transcription = ""
    points = []

    numPoints = 4

    if LTRB:
        numPoints = 4

        if withTranscription and withConfidence:
            m = re.match(
                r"^\s*(-?[0-9]+)\s*,\s*(-?[0-9]+)\s*,\s*([0-9]+)\s*,\s*([0-9]+)\s*,\s*([0-1].?[0-9]*)\s*,(.*)$",
                line,
            )
            if m == None:
                m = re.match(
                    r"^\s*(-?[0-9]+)\s*,\s*(-?[0-9]+)\s*,\s*([0-9]+)\s*,\s*([0-9]+)\s*,\s*([0-1].?[0-9]*)\s*,(.*)$",
                    line,
                )
                raise Exception(
                    "Format incorrect. Should be: xmin,ymin,xmax,ymax,confidence,transcription"
                )
        elif withConfidence:
            m = re.match(
                r"^\s*(-?[0-9]+)\s*,\s*(-?[0-9]+)\s*,\s*([0-9]+)\s*,\s*([0-9]+)\s*,\s*([0-1].?[0-9]*)\s*$",
                line,
            )
            if m == None:
                raise Exception(
                    "Format incorrect. Should be: xmin,ymin,xmax,ymax,confidence"
                )
        elif withTranscription:
            m = re.match(
                r"^\s*(-?[0-9]+)\s*,\s*(-?[0-9]+)\s*,\s*([0-9]+)\s*,\s*([0-9]+)\s*,(.*)$",
                line,
            )
            if m == None:
                raise Exception(
                    "Format incorrect. Should be: xmin,ymin,xmax,ymax,transcription"
                )
        else:
            m = re.match(
                r"^\s*(-?[0-9]+)\s*,\s*(-?[0-9]+)\s*,\s*([0-9]+)\s*,\s*([0-9]+)\s*,?\s*$",
                line,
            )
            if m == None:
                raise Exception("Format incorrect. Should be: xmin,ymin,xmax,ymax")

        xmin = int(m.group(1))
        ymin = int(m.group(2))
        xmax = int(m.group(3))
        ymax = int(m.group(4))
        if xmax < xmin:
            raise Exception("Xmax value (%s) not valid (Xmax < Xmin)." % (xmax))
        if ymax < ymin:
            raise Exception("Ymax value (%s)  not valid (Ymax < Ymin)." % (ymax))

        points = [float(m.group(i)) for i in range(1, (numPoints + 1))]

        if imWidth > 0 and imHeight > 0:
            validate_point_inside_bounds(xmin, ymin, imWidth, imHeight)
            validate_point_inside_bounds(xmax, ymax, imWidth, imHeight)

    else:
        numPoints = 8

        if withTranscription and withConfidence:
            m = re.match(
                r"^\s*(-?[0-9]+)\s*,\s*(-?[0-9]+)\s*,\s*(-?[0-9]+)\s*,\s*(-?[0-9]+)\s*,\s*(-?[0-9]+)\s*,\s*(-?[0-9]+)\s*,\s*(-?[0-9]+)\s*,\s*(-?[0-9]+)\s*,\s*([0-1].?[0-9]*)\s*,(.*)$",
                line,
            )
            if m == None:
                raise Exception(
                    "Format incorrect. Should be: x1,y1,x2,y2,x3,y3,x4,y4,confidence,transcription"
                )
        elif withConfidence:
            m = re.match(
                r"^\s*(-?[0-9]+)\s*,\s*(-?[0-9]+)\s*,\s*(-?[0-9]+)\s*,\s*(-?[0-9]+)\s*,\s*(-?[0-9]+)\s*,\s*(-?[0-9]+)\s*,\s*(-?[0-9]+)\s*,\s*(-?[0-9]+)\s*,\s*([0-1].?[0-9]*)\s*$",
                line,
            )
            if m == None:
                raise Exception(
                    "Format incorrect. Should be: x1,y1,x2,y2,x3,y3,x4,y4,confidence"
                )
        elif withTranscription:
            m = re.match(
                r"^\s*(-?[0-9]+)\s*,\s*(-?[0-9]+)\s*,\s*(-?[0-9]+)\s*,\s*(-?[0-9]+)\s*,\s*(-?[0-9]+)\s*,\s*(-?[0-9]+)\s*,\s*(-?[0-9]+)\s*,\s*(-?[0-9]+)\s*,(.*)$",
                line,
            )
            if m == None:
                raise Exception(
                    "Format incorrect. Should be: x1,y1,x2,y2,x3,y3,x4,y4,transcription"
                )
        else:
            m = re.match(
                r"^\s*(-?[0-9]+)\s*,\s*(-?[0-9]+)\s*,\s*(-?[0-9]+)\s*,\s*(-?[0-9]+)\s*,\s*(-?[0-9]+)\s*,\s*(-?[0-9]+)\s*,\s*(-?[0-9]+)\s*,\s*(-?[0-9]+)\s*$",
                line,
            )
            if m == None:
                raise Exception("Format incorrect. Should be: x1,y1,x2,y2,x3,y3,x4,y4")

        points = [float(m.group(i)) for i in range(1, (numPoints + 1))]

        points = order_points_clockwise(np.array(points).reshape(-1, 2)).reshape(-1)
        validate_clockwise_points(points)

        if imWidth > 0 and imHeight > 0:
            validate_point_inside_bounds(points[0], points[1], imWidth, imHeight)
            validate_point_inside_bounds(points[2], points[3], imWidth, imHeight)
            validate_point_inside_bounds(points[4], points[5], imWidth, imHeight)
            validate_point_inside_bounds(points[6], points[7], imWidth, imHeight)

    if withConfidence:
        try:
            confidence = float(m.group(numPoints + 1))
        except ValueError:
            raise Exception("Confidence value must be a float")

    if withTranscription:
        posTranscription = numPoints + (2 if withConfidence else 1)
        transcription = m.group(posTranscription)
        m2 = re.match(r"^\s*\"(.*)\"\s*$", transcription)
        if (
            m2 != None
        ):  # Transcription with double quotes, we extract the value and replace escaped characters
            transcription = m2.group(1).replace("\\\\", "\\").replace('\\"', '"')

    return points, confidence, transcription