def thumbnail_img(filename, blob):
    """
    Generate thumbnail image bytes for PDF, image, or PPT. MySQL LongText max length is 65535.

    Robustness and edge cases:
    - Rejects None, empty, or oversized blob to avoid DoS/OOM.
    - Uses basename for type detection (handles paths like "a/b/c.pdf").
    - Catches corrupt or malformed files and returns None instead of raising.
    - Normalizes PIL image mode (e.g. RGBA -> RGB) for safe PNG export.
    """
    if blob is None:
        return None
    try:
        blob_len = len(blob)
    except TypeError:
        return None
    if blob_len == 0 or blob_len > MAX_BLOB_SIZE_THUMBNAIL:
        return None

    normalized, ok = _normalize_filename_for_type(filename)
    if not ok:
        return None
    filename = normalized

    if re.match(r".*\.pdf$", filename):
        try:
            with sys.modules[LOCK_KEY_pdfplumber]:
                pdf = pdfplumber.open(BytesIO(blob))
                if not pdf.pages:
                    pdf.close()
                    return None
                buffered = BytesIO()
                resolution = 32
                img = None
                for _ in range(10):
                    pdf.pages[0].to_image(resolution=resolution).annotated.save(buffered, format="png")
                    img = buffered.getvalue()
                    if len(img) >= 64000 and resolution >= 2:
                        resolution = resolution / 2
                        buffered = BytesIO()
                    else:
                        break
                pdf.close()
                return img
        except Exception:
            return None

    if re.match(r".*\.(jpg|jpeg|png|tif|gif|icon|ico|webp)$", filename):
        try:
            image = Image.open(BytesIO(blob))
            image.load()
            if image.mode in ("RGBA", "P", "LA"):
                image = image.convert("RGB")
            image.thumbnail((30, 30))
            buffered = BytesIO()
            image.save(buffered, format="png")
            return buffered.getvalue()
        except Exception:
            return None

    # PPT/PPTX thumbnail would require a licensed library; skip and return None.
    if re.match(r".*\.(ppt|pptx)$", filename):
        return None

    return None