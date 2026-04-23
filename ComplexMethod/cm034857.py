def get_tl_line_values_from_file_contents(
    content,
    CRLF=True,
    LTRB=True,
    withTranscription=False,
    withConfidence=False,
    imWidth=0,
    imHeight=0,
    sort_by_confidences=True,
):
    """
    Returns all points, confindences and transcriptions of a file in lists. Valid line formats:
    xmin,ymin,xmax,ymax,[confidence],[transcription]
    x1,y1,x2,y2,x3,y3,x4,y4,[confidence],[transcription]
    """
    pointsList = []
    transcriptionsList = []
    confidencesList = []

    lines = content.split("\r\n" if CRLF else "\n")
    for line in lines:
        line = line.replace("\r", "").replace("\n", "")
        if line != "":
            points, confidence, transcription = get_tl_line_values(
                line, LTRB, withTranscription, withConfidence, imWidth, imHeight
            )
            pointsList.append(points)
            transcriptionsList.append(transcription)
            confidencesList.append(confidence)

    if withConfidence and len(confidencesList) > 0 and sort_by_confidences:
        import numpy as np

        sorted_ind = np.argsort(-np.array(confidencesList))
        confidencesList = [confidencesList[i] for i in sorted_ind]
        pointsList = [pointsList[i] for i in sorted_ind]
        transcriptionsList = [transcriptionsList[i] for i in sorted_ind]

    return pointsList, confidencesList, transcriptionsList