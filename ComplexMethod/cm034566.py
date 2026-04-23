def load_cookies_from_browsers(domain_name: str,
                               raise_requirements_error: bool = True,
                               single_browser: Optional[str] = None) -> Cookies:
    """Helper to load cookies from all supported browsers."""
    if not has_browser_cookie3:
        if raise_requirements_error:
            raise MissingRequirementsError('Install "browser_cookie3" package')
        return {}

    cookies = {}
    all_cookies = {}
    for cookie_fn in BROWSERS:
        if domain_name in CookiesConfig.cookies:
            all_cookies[cookie_fn.__name__] = {"config": CookiesConfig.cookies.get(domain_name, {})}
        else:
            all_cookies[cookie_fn.__name__] = {}
        try:
            cookie_jar = cookie_fn(domain_name=domain_name)
            for cookie in cookie_jar:
                if cookie.name not in cookies and (not cookie.expires or cookie.expires > time.time()):
                    cookies[cookie.name] = cookie.value
                    all_cookies[cookie_fn.__name__][cookie.name] = cookie.value
            if len(all_cookies[cookie_fn.__name__]) > 0:
                debug.log(f"Total cookies loaded for {domain_name} from {cookie_fn.__name__}: {len(all_cookies[cookie_fn.__name__])}")
            if single_browser is True and cookie_jar:
                break
        except BrowserCookieError:
            pass
        except KeyboardInterrupt:
            debug.error("Cookie loading interrupted by user.")
            break
        except Exception as e:
            debug.error(f"Error reading cookies from {cookie_fn.__name__} for {domain_name}: {type(e).__name__}: {e}")
    if single_browser == "all":
        return all_cookies
    return cookies