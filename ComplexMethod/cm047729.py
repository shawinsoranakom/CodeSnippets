def average_dominant_color(colors, mitigate=175, max_margin=140):
    """This function is used to calculate the dominant colors when given a list of colors

    There are 5 steps:

    1) Select dominant colors (highest count), isolate its values and remove
       it from the current color set.
    2) Set margins according to the prevalence of the dominant color.
    3) Evaluate the colors. Similar colors are grouped in the dominant set
       while others are put in the "remaining" list.
    4) Calculate the average color for the dominant set. This is done by
       averaging each band and joining them into a tuple.
    5) Mitigate final average and convert it to hex

    :param colors: list of tuples having:

        0. color count in the image
        1. actual color: tuple(R, G, B, A)

        -> these can be extracted from a PIL image using
        :meth:`~PIL.Image.Image.getcolors`
    :param mitigate: maximum value a band can reach
    :param max_margin: maximum difference from one of the dominant values
    :returns: a tuple with two items:

        0. the average color of the dominant set as: tuple(R, G, B)
        1. list of remaining colors, used to evaluate subsequent dominant colors
    """
    dominant_color = max(colors)
    dominant_rgb = dominant_color[1][:3]
    dominant_set = [dominant_color]
    remaining = []

    margins = [max_margin * (1 - dominant_color[0] /
                             sum([col[0] for col in colors]))] * 3

    colors.remove(dominant_color)

    for color in colors:
        rgb = color[1]
        if (rgb[0] < dominant_rgb[0] + margins[0] and rgb[0] > dominant_rgb[0] - margins[0] and
            rgb[1] < dominant_rgb[1] + margins[1] and rgb[1] > dominant_rgb[1] - margins[1] and
                rgb[2] < dominant_rgb[2] + margins[2] and rgb[2] > dominant_rgb[2] - margins[2]):
            dominant_set.append(color)
        else:
            remaining.append(color)

    dominant_avg = []
    for band in range(3):
        avg = total = 0
        for color in dominant_set:
            avg += color[0] * color[1][band]
            total += color[0]
        dominant_avg.append(int(avg / total))

    final_dominant = []
    brightest = max(dominant_avg)
    for color in range(3):
        value = dominant_avg[color] / (brightest / mitigate) if brightest > mitigate else dominant_avg[color]
        final_dominant.append(int(value))

    return tuple(final_dominant), remaining