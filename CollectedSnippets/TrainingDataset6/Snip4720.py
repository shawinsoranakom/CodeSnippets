def get_app():
    with pytest.warns(DeprecationWarning):
        from docs_src.events.tutorial002_py310 import app
    yield app