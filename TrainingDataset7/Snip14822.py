def csp_report_only_override(config):
    """Override the Content-Security-Policy-Report-Only header for a view."""
    return _make_csp_decorator("_csp_ro_config", config)