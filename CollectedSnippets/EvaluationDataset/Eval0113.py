def rectangular_to_polar(real: float, img: float) -> tuple[float, float]:

    mod = round(math.sqrt((real**2) + (img**2)), 2)
    ang = round(math.degrees(math.atan2(img, real)), 2)
    return (mod, ang)
