def read_info_from_image(image: Image.Image) -> tuple[str | None, dict]:
    items = (image.info or {}).copy()

    geninfo = items.pop('parameters', None)

    if "exif" in items:
        exif_data = items["exif"]
        try:
            exif = piexif.load(exif_data)
        except OSError:
            # memory / exif was not valid so piexif tried to read from a file
            exif = None
        exif_comment = (exif or {}).get("Exif", {}).get(piexif.ExifIFD.UserComment, b'')
        try:
            exif_comment = piexif.helper.UserComment.load(exif_comment)
        except ValueError:
            exif_comment = exif_comment.decode('utf8', errors="ignore")

        if exif_comment:
            geninfo = exif_comment
    elif "comment" in items: # for gif
        if isinstance(items["comment"], bytes):
            geninfo = items["comment"].decode('utf8', errors="ignore")
        else:
            geninfo = items["comment"]

    for field in IGNORED_INFO_KEYS:
        items.pop(field, None)

    if items.get("Software", None) == "NovelAI":
        try:
            json_info = json.loads(items["Comment"])
            sampler = sd_samplers.samplers_map.get(json_info["sampler"], "Euler a")

            geninfo = f"""{items["Description"]}
Negative prompt: {json_info["uc"]}
Steps: {json_info["steps"]}, Sampler: {sampler}, CFG scale: {json_info["scale"]}, Seed: {json_info["seed"]}, Size: {image.width}x{image.height}, Clip skip: 2, ENSD: 31337"""
        except Exception:
            errors.report("Error parsing NovelAI image generation parameters", exc_info=True)

    return geninfo, items