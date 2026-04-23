def render(filename = "home", download_url: str = GITHUB_URL):
    if download_url == GITHUB_URL:
        filename += ("" if "." in filename else ".html")
    html = None
    is_temp = False
    if os.path.exists(DIST_DIR) and not request.args.get("debug"):
        path = os.path.abspath(os.path.join(os.path.dirname(DIST_DIR), filename))
        if os.path.exists(path):
            if download_url == GITHUB_URL:
                with open(path, 'r', encoding='utf-8') as f:
                    html = f.read()
                is_temp = True
            else:
                return send_from_directory(os.path.dirname(path), os.path.basename(path))
    try:
        latest_version = version.utils.latest_version
    except VersionNotFoundError:
        latest_version = version.utils.current_version
    today = datetime.today().strftime('%Y-%m-%d')
    cache_dir = os.path.join(get_cookies_dir(), ".gui_cache", today)
    if not request.args.get("session_token"):
        latest_version = str(latest_version) + quote(unquote(request.query_string.decode()))
    cache_file = os.path.join(cache_dir, f"{secure_filename(f'{version.utils.current_version}-{latest_version}')}.{secure_filename(filename)}")
    if os.path.isfile(cache_file + ".js"):
        cache_file += ".js"
    if not os.path.exists(cache_file):
        if os.access(cache_file, os.W_OK):
            is_temp = True
        else:
            os.makedirs(cache_dir, exist_ok=True)
        if html is None:
            try:
                response = requests.get(f"{download_url}{filename}")
                response.raise_for_status()
            except requests.RequestException:
                try:
                    response = requests.get(f"{DOWNLOAD_URL}{filename}")
                    response.raise_for_status()
                except requests.RequestException:
                    found = None
                    for root, _, files in os.walk(cache_dir):
                        for file in files:
                            if file.startswith(secure_filename(filename)):
                                found = os.path.abspath(root), file
                        break
                    if found:
                        return send_from_directory(found[0], found[1])
                    else:
                        raise
            if not cache_file.endswith(".js") and response.headers.get("Content-Type", "").startswith("application/javascript"):
                cache_file += ".js"
            html = response.text
            html = html.replace('"../dist/', f"\"{STATIC_URL}dist/")
            html = html.replace('"/dist/', f"\"{STATIC_URL}dist/")
            html = html.replace('"dist/', f"\"{STATIC_URL}dist/")
        # html = html.replace(JSDELIVR_URL, "/")
        html = html.replace("{{ v }}", latest_version)
        if is_temp:
            return html
        with open(cache_file, 'w', encoding='utf-8') as f:
            f.write(html)
    return send_from_directory(os.path.abspath(cache_dir), os.path.basename(cache_file))