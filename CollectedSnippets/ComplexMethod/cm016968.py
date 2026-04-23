def get_quality_mode(poly_count):
    polycount = poly_count.split("-")
    poly = polycount[1]
    count = polycount[0]
    if poly == "Triangle":
        mesh_mode = "Raw"
    elif poly == "Quad":
        mesh_mode = "Quad"
    else:
        mesh_mode = "Quad"

    if count == "4K":
        quality_override = 4000
    elif count == "8K":
        quality_override = 8000
    elif count == "18K":
        quality_override = 18000
    elif count == "50K":
        quality_override = 50000
    elif count == "2K":
        quality_override = 2000
    elif count == "20K":
        quality_override = 20000
    elif count == "150K":
        quality_override = 150000
    elif count == "500K":
        quality_override = 500000
    else:
        quality_override = 18000

    return mesh_mode, quality_override