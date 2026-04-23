def focal_point(im, settings):
    corner_points = image_corner_points(im, settings) if settings.corner_points_weight > 0 else []
    entropy_points = image_entropy_points(im, settings) if settings.entropy_points_weight > 0 else []
    face_points = image_face_points(im, settings) if settings.face_points_weight > 0 else []

    pois = []

    weight_pref_total = 0
    if corner_points:
        weight_pref_total += settings.corner_points_weight
    if entropy_points:
        weight_pref_total += settings.entropy_points_weight
    if face_points:
        weight_pref_total += settings.face_points_weight

    corner_centroid = None
    if corner_points:
        corner_centroid = centroid(corner_points)
        corner_centroid.weight = settings.corner_points_weight / weight_pref_total
        pois.append(corner_centroid)

    entropy_centroid = None
    if entropy_points:
        entropy_centroid = centroid(entropy_points)
        entropy_centroid.weight = settings.entropy_points_weight / weight_pref_total
        pois.append(entropy_centroid)

    face_centroid = None
    if face_points:
        face_centroid = centroid(face_points)
        face_centroid.weight = settings.face_points_weight / weight_pref_total
        pois.append(face_centroid)

    average_point = poi_average(pois, settings)

    if settings.annotate_image:
        d = ImageDraw.Draw(im)
        max_size = min(im.width, im.height) * 0.07
        if corner_centroid is not None:
            color = BLUE
            box = corner_centroid.bounding(max_size * corner_centroid.weight)
            d.text((box[0], box[1] - 15), f"Edge: {corner_centroid.weight:.02f}", fill=color)
            d.ellipse(box, outline=color)
            if len(corner_points) > 1:
                for f in corner_points:
                    d.rectangle(f.bounding(4), outline=color)
        if entropy_centroid is not None:
            color = "#ff0"
            box = entropy_centroid.bounding(max_size * entropy_centroid.weight)
            d.text((box[0], box[1] - 15), f"Entropy: {entropy_centroid.weight:.02f}", fill=color)
            d.ellipse(box, outline=color)
            if len(entropy_points) > 1:
                for f in entropy_points:
                    d.rectangle(f.bounding(4), outline=color)
        if face_centroid is not None:
            color = RED
            box = face_centroid.bounding(max_size * face_centroid.weight)
            d.text((box[0], box[1] - 15), f"Face: {face_centroid.weight:.02f}", fill=color)
            d.ellipse(box, outline=color)
            if len(face_points) > 1:
                for f in face_points:
                    d.rectangle(f.bounding(4), outline=color)

        d.ellipse(average_point.bounding(max_size), outline=GREEN)

    return average_point