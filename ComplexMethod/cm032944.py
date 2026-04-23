def _is_sensitive_url(url: str) -> bool:
    """Return True if URL is one of the configured OAuth endpoints."""
    # Collect known sensitive endpoint URLs from settings
    oauth_urls = set()
    # GitHub OAuth endpoints
    try:
        if settings.GITHUB_OAUTH is not None:
            url_val = settings.GITHUB_OAUTH.get("url")
            if url_val:
                oauth_urls.add(url_val)
    except Exception:
        pass
    # Feishu OAuth endpoints
    try:
        if settings.FEISHU_OAUTH is not None:
            for k in ("app_access_token_url", "user_access_token_url"):
                url_val = settings.FEISHU_OAUTH.get(k)
                if url_val:
                    oauth_urls.add(url_val)
    except Exception:
        pass
    # Defensive normalization: compare only scheme+netloc+path
    url_obj = urlparse(url)
    for sensitive_url in oauth_urls:
        sensitive_obj = urlparse(sensitive_url)
        if (url_obj.scheme, url_obj.netloc, url_obj.path) == (sensitive_obj.scheme, sensitive_obj.netloc, sensitive_obj.path):
            return True
    return False