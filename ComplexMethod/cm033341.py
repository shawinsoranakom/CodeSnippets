async def parse():
    req = await get_request_json()
    url = req.get("url", "")
    if url:
        if not is_valid_url(url):
            return get_json_result(data=False, message="The URL format is invalid", code=RetCode.ARGUMENT_ERROR)
        download_path = os.path.join(get_project_base_directory(), "logs/downloads")
        os.makedirs(download_path, exist_ok=True)
        from seleniumwire.webdriver import Chrome, ChromeOptions

        options = ChromeOptions()
        options.add_argument("--headless")
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_experimental_option("prefs", {"download.default_directory": download_path, "download.prompt_for_download": False, "download.directory_upgrade": True, "safebrowsing.enabled": True})
        driver = Chrome(options=options)
        driver.get(url)
        res_headers = [r.response.headers for r in driver.requests if r and r.response]
        if len(res_headers) > 1:
            sections = RAGFlowHtmlParser().parser_txt(driver.page_source)
            driver.quit()
            return get_json_result(data="\n".join(sections))

        class File:
            filename: str
            filepath: str

            def __init__(self, filename, filepath):
                self.filename = filename
                self.filepath = filepath

            def read(self):
                with open(self.filepath, "rb") as f:
                    return f.read()

        r = re.search(r"filename=\"([^\"]+)\"", str(res_headers))
        if not r or not r.group(1):
            return get_json_result(data=False, message="Can't not identify downloaded file", code=RetCode.ARGUMENT_ERROR)
        filename = r.group(1).strip()
        if not _is_safe_download_filename(filename):
            return get_json_result(data=False, message="Invalid downloaded filename", code=RetCode.ARGUMENT_ERROR)
        filepath = os.path.join(download_path, filename)
        f = File(filename, filepath)
        txt = FileService.parse_docs([f], current_user.id)
        return get_json_result(data=txt)

    files = await request.files
    if "file" not in files:
        return get_json_result(data=False, message="No file part!", code=RetCode.ARGUMENT_ERROR)

    file_objs = files.getlist("file")
    txt = FileService.parse_docs(file_objs, current_user.id)

    return get_json_result(data=txt)