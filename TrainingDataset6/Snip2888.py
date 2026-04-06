def test_no_multipart_installed_multi_form(monkeypatch):
    monkeypatch.setattr("python_multipart.__version__", "0.0.12")
    with warnings.catch_warnings(record=True):
        warnings.simplefilter("always")
        monkeypatch.delattr("multipart.__version__", raising=False)
        with pytest.raises(RuntimeError, match=multipart_not_installed_error):
            app = FastAPI()

            @app.post("/")
            async def root(username: str = Form(), password: str = Form()):
                return username