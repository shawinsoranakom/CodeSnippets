def save_image_with_geninfo(image, geninfo, filename, extension=None, existing_pnginfo=None, pnginfo_section_name='parameters'):
    """
    Saves image to filename, including geninfo as text information for generation info.
    For PNG images, geninfo is added to existing pnginfo dictionary using the pnginfo_section_name argument as key.
    For JPG images, there's no dictionary and geninfo just replaces the EXIF description.
    """

    if extension is None:
        extension = os.path.splitext(filename)[1]

    image_format = Image.registered_extensions()[extension]

    if extension.lower() == '.png':
        existing_pnginfo = existing_pnginfo or {}
        if opts.enable_pnginfo:
            existing_pnginfo[pnginfo_section_name] = geninfo

        if opts.enable_pnginfo:
            pnginfo_data = PngImagePlugin.PngInfo()
            for k, v in (existing_pnginfo or {}).items():
                pnginfo_data.add_text(k, str(v))
        else:
            pnginfo_data = None

        image.save(filename, format=image_format, quality=opts.jpeg_quality, pnginfo=pnginfo_data)

    elif extension.lower() in (".jpg", ".jpeg", ".webp"):
        if image.mode == 'RGBA':
            image = image.convert("RGB")
        elif image.mode == 'I;16':
            image = image.point(lambda p: p * 0.0038910505836576).convert("RGB" if extension.lower() == ".webp" else "L")

        image.save(filename, format=image_format, quality=opts.jpeg_quality, lossless=opts.webp_lossless)

        if opts.enable_pnginfo and geninfo is not None:
            exif_bytes = piexif.dump({
                "Exif": {
                    piexif.ExifIFD.UserComment: piexif.helper.UserComment.dump(geninfo or "", encoding="unicode")
                },
            })

            piexif.insert(exif_bytes, filename)
    elif extension.lower() == '.avif':
        if opts.enable_pnginfo and geninfo is not None:
            exif_bytes = piexif.dump({
                "Exif": {
                    piexif.ExifIFD.UserComment: piexif.helper.UserComment.dump(geninfo or "", encoding="unicode")
                },
            })
        else:
            exif_bytes = None

        image.save(filename,format=image_format, quality=opts.jpeg_quality, exif=exif_bytes)
    elif extension.lower() == ".gif":
        image.save(filename, format=image_format, comment=geninfo)
    else:
        image.save(filename, format=image_format, quality=opts.jpeg_quality)