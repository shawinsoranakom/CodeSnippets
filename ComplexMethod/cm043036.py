def test_chanel(label, proxy=None, use_cffi=False):
    url = "https://www.chanel.com/us/fashion/handbags/c/1x1x1/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    }
    print(f"\n{'='*60}")
    print(f"TEST: {label}")
    try:
        if use_cffi:
            from curl_cffi import requests as cffi_requests
            kwargs = {"url": url, "headers": headers, "impersonate": "chrome", "timeout": 30, "allow_redirects": True}
            if proxy:
                kwargs["proxies"] = {"https": proxy, "http": proxy}
            resp = cffi_requests.get(**kwargs)
        else:
            kwargs = {"url": url, "headers": headers, "timeout": 30, "allow_redirects": True}
            if proxy:
                kwargs["proxies"] = {"https": proxy, "http": proxy}
            resp = requests.get(**kwargs)

        blocked = "Access Denied" in resp.text
        print(f"  Status: {resp.status_code}")
        print(f"  Size: {len(resp.text):,} bytes")
        print(f"  Result: {'BLOCKED' if blocked else 'SUCCESS' if resp.status_code == 200 and len(resp.text) > 10000 else 'UNCLEAR'}")
        if not blocked and resp.status_code == 200:
            print(f"  First 300 chars: {resp.text[:300]}")
    except Exception as e:
        print(f"  ERROR: {e}")