def clear_site_cache(sender, **kwargs):
    """
    Clear the cache (if primed) each time a site is saved or deleted.
    """
    instance = kwargs["instance"]
    using = kwargs["using"]
    try:
        del SITE_CACHE[instance.pk]
    except KeyError:
        pass
    try:
        del SITE_CACHE[Site.objects.using(using).get(pk=instance.pk).domain]
    except (KeyError, Site.DoesNotExist):
        pass