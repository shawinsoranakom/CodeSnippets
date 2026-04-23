def test_parse_url_and_multipart_matrix_unit(self, document_app_module, monkeypatch, tmp_path):
        module = document_app_module

        async def req_invalid_url():
            return {"url": "not-a-url"}

        monkeypatch.setattr(module, "get_request_json", req_invalid_url)
        monkeypatch.setattr(module, "is_valid_url", lambda _url: False)
        res = _run(module.parse())
        assert res["code"] == module.RetCode.ARGUMENT_ERROR
        assert res["message"] == "The URL format is invalid"

        webdriver_mod = ModuleType("seleniumwire.webdriver")

        class _FakeChromeOptions:
            def __init__(self):
                self.args = []
                self.experimental = {}

            def add_argument(self, arg):
                self.args.append(arg)

            def add_experimental_option(self, key, value):
                self.experimental[key] = value

        class _Req:
            def __init__(self, headers):
                self.response = SimpleNamespace(headers=headers)

        class _FakeDriver:
            def __init__(self, requests, page_source):
                self.requests = requests
                self.page_source = page_source
                self.quit_called = False
                self.visited = []
                self.options = None

            def get(self, url):
                self.visited.append(url)

            def quit(self):
                self.quit_called = True

        queue = []
        created = []

        def _fake_chrome(options=None):
            driver = queue.pop(0)
            driver.options = options
            created.append(driver)
            return driver

        webdriver_mod.Chrome = _fake_chrome
        webdriver_mod.ChromeOptions = _FakeChromeOptions

        seleniumwire_mod = ModuleType("seleniumwire")
        seleniumwire_mod.webdriver = webdriver_mod
        monkeypatch.setitem(sys.modules, "seleniumwire", seleniumwire_mod)
        monkeypatch.setitem(sys.modules, "seleniumwire.webdriver", webdriver_mod)
        monkeypatch.setattr(module, "get_project_base_directory", lambda: str(tmp_path))
        monkeypatch.setattr(module, "is_valid_url", lambda _url: True)

        class _Parser:
            def parser_txt(self, page_source):
                assert "page" in page_source
                return ["section1", "section2"]

        monkeypatch.setattr(module, "RAGFlowHtmlParser", lambda: _Parser())
        queue.append(_FakeDriver([_Req({"x": "1"}), _Req({"y": "2"})], "<html>page</html>"))

        async def req_url_html():
            return {"url": "http://example.com/html"}

        monkeypatch.setattr(module, "get_request_json", req_url_html)
        res = _run(module.parse())
        assert res["code"] == 0
        assert res["data"] == "section1\nsection2"
        assert created[-1].quit_called is True

        (tmp_path / "logs" / "downloads").mkdir(parents=True, exist_ok=True)
        (tmp_path / "logs" / "downloads" / "doc.txt").write_bytes(b"downloaded-bytes")
        queue.append(_FakeDriver([_Req({"content-disposition": 'attachment; filename="doc.txt"'})], "<html>file</html>"))
        captured = {}

        def parse_docs_read(files, _uid):
            captured["filename"] = files[0].filename
            captured["content"] = files[0].read()
            return "parsed-download"

        monkeypatch.setattr(module.FileService, "parse_docs", parse_docs_read)

        async def req_url_file():
            return {"url": "http://example.com/file"}

        monkeypatch.setattr(module, "get_request_json", req_url_file)
        res = _run(module.parse())
        assert res["code"] == 0
        assert res["data"] == "parsed-download"
        assert captured["filename"] == "doc.txt"
        assert captured["content"] == b"downloaded-bytes"

        async def req_no_url():
            return {}

        monkeypatch.setattr(module, "get_request_json", req_no_url)
        monkeypatch.setattr(module, "request", _DummyRequest(files=_DummyFiles()))
        res = _run(module.parse())
        assert res["code"] == module.RetCode.ARGUMENT_ERROR
        assert res["message"] == "No file part!"

        monkeypatch.setattr(module, "request", _DummyRequest(files=_DummyFiles({"file": [_DummyFile("f1.txt")]})))
        monkeypatch.setattr(module.FileService, "parse_docs", lambda _files, _uid: "parsed-upload")
        res = _run(module.parse())
        assert res["code"] == 0
        assert res["data"] == "parsed-upload"