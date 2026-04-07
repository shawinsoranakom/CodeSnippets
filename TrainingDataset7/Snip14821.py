def csp_override(config):
    """Override the Content-Security-Policy header for a view."""
    return _make_csp_decorator("_csp_config", config)