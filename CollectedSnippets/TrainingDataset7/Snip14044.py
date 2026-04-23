def is_valid_path(path, urlconf=None):
    """
    Return the ResolverMatch if the given path resolves against the default URL
    resolver, False otherwise. This is a convenience method to make working
    with "is this a match?" cases easier, avoiding try...except blocks.
    """
    try:
        return resolve(path, urlconf)
    except Resolver404:
        return False