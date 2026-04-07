def get_perm(Model, codename):
    """Return the permission object, for the Model"""
    ct = ContentType.objects.get_for_model(Model, for_concrete_model=False)
    return Permission.objects.get(content_type=ct, codename=codename)