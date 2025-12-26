def approximately_equal_hsv(hsv_1: list[float], hsv_2: list[float]) -> bool:

    check_hue = abs(hsv_1[0] - hsv_2[0]) < 0.2
    check_saturation = abs(hsv_1[1] - hsv_2[1]) < 0.002
    check_value = abs(hsv_1[2] - hsv_2[2]) < 0.002

    return check_hue and check_saturation and check_value
