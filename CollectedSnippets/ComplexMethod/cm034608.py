async def clear_cookies_for_url(browser: Browser, url: str, ignore_cookies: list[str] = None):
    host = urlparse(url).hostname
    if not host:
        raise ValueError(f"Bad url: {url}")

    if ignore_cookies is None:
        ignore_cookies = []
    tab = browser.main_tab  # any open tab is fine
    cookies = await browser.cookies.get_all()  # returns CDP cookies :contentReference[oaicite:2]{index=2}
    for c in cookies:
        dom = (c.domain or "").lstrip(".")
        if dom and (host == dom or host.endswith("." + dom)):
            if c.name in ignore_cookies:
                continue
            await tab.send(
                nodriver.cdp.network.delete_cookies(
                    name=c.name,
                    domain=dom,  # exact domain :contentReference[oaicite:3]{index=3}
                    path=c.path,  # exact path :contentReference[oaicite:4]{index=4}
                    # partition_key=c.partition_key,  # if you use partitioned cookies
                )
            )