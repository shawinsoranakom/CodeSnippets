def test_old_multipart_installed(monkeypatch):
    monkeypatch.setattr("python_multipart.__version__", "0.0.12")
    with warnings.catch_warnings(record=True):
        warnings.simplefilter("always")
        app = FastAPI()

        @app.post("/")
        async def root(username: str = Form()):
            return username