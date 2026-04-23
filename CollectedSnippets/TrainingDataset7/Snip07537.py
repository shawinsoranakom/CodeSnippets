def kmz(request, label, model, field_name=None, using=DEFAULT_DB_ALIAS):
    """
    Return KMZ for the given app label, model, and field name.
    """
    return kml(request, label, model, field_name, compress=True, using=using)