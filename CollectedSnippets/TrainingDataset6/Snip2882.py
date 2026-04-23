def test_incorrect_multipart_installed_file_bytes(monkeypatch):
    monkeypatch.setattr("python_multipart.__version__", "0.0.12")
    with warnings.catch_warnings(record=True):
        warnings.simplefilter("always")
        monkeypatch.delattr("multipart.multipart.parse_options_header", raising=False)
    with pytest.raises(RuntimeError, match=multipart_incorrect_install_error):
        app = FastAPI()

        @app.post("/")
        async def root(f: bytes = File()):
            return f