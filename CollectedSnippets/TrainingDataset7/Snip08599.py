def reset_urlconf(sender, **kwargs):
    """Reset the URLconf after each request is finished."""
    set_urlconf(None)