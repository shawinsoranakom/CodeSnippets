def compress_kml(kml):
    "Return compressed KMZ from the given KML string."
    kmz = BytesIO()
    with zipfile.ZipFile(kmz, "a", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("doc.kml", kml.encode(settings.DEFAULT_CHARSET))
    kmz.seek(0)
    return kmz.read()