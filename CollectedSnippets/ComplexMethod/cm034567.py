def read_cookie_files(dir_path: Optional[str] = None, domains_filter: Optional[List[str]] = None) -> None:
    """
    Load cookies from .har and .json files in a directory.
    """
    dir_path = dir_path or CookiesConfig.cookies_dir
    if not os.access(dir_path, os.R_OK):
        debug.log(f"Read cookies: {dir_path} dir is not readable")
        return

    # Optionally load environment variables
    try:
        from dotenv import load_dotenv
        env_path = os.path.join(dir_path, ".env")
        load_dotenv(env_path, override=True)
        debug.log(f"Loaded env vars from {env_path}: {os.path.exists(env_path)}")
    except ImportError:
        debug.error("Warning: 'python-dotenv' is not installed. Env vars not loaded.")

    AppConfig.load_from_env()

    BrowserConfig.load_from_env()
    if BrowserConfig.port:
        BrowserConfig.port = int(BrowserConfig.port)
        debug.log(f"Using browser: {BrowserConfig.host}:{BrowserConfig.port}")
    BrowserConfig.impersonate = os.environ.get("G4F_BROWSER_IMPERSONATE", BrowserConfig.impersonate)
    if os.path.exists(os.path.join(dir_path, ".browser_is_open")):
        os.remove(os.path.join(dir_path, ".browser_is_open"))

    har_files, json_files = [], []
    for root, _, files in os.walk(dir_path):
        for file in files:
            if file.endswith(".har"):
                har_files.append(os.path.join(root, file))
            elif file.endswith(".json"):
                json_files.append(os.path.join(root, file))
        break  # Do not recurse

    CookiesConfig.cookies.clear()

    # Load cookies from files
    for path in har_files:
        for domain, cookies in _parse_har_file(path).items():
            if not domains_filter or domain in domains_filter:
                CookiesConfig.cookies[domain] = cookies
                debug.log(f"Cookies added: {len(cookies)} from {domain}")

    for path in json_files:
        for domain, cookies in _parse_json_cookie_file(path).items():
            if not domains_filter or domain in domains_filter:
                CookiesConfig.cookies[domain] = cookies
                debug.log(f"Cookies added: {len(cookies)} from {domain}")

    # Load custom model routing config (config.yaml)
    try:
        from .providers.config_provider import RouterConfig
        config_path = os.path.join(dir_path, "config.yaml")
        RouterConfig.load(config_path)
    except Exception as e:
        config_path = os.path.join(dir_path, "config.yaml")
        debug.error(f"config.yaml: Failed to load routing config from {config_path}:", e)