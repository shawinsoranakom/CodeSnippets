def test_static_file(self, app, req_ctx):
        # Default max_age is None.

        # Test with static file handler.
        with app.send_static_file("index.html") as rv:
            assert rv.cache_control.max_age is None

        # Test with direct use of send_file.
        with flask.send_file("static/index.html") as rv:
            assert rv.cache_control.max_age is None

        app.config["SEND_FILE_MAX_AGE_DEFAULT"] = 3600

        # Test with static file handler.
        with app.send_static_file("index.html") as rv:
            assert rv.cache_control.max_age == 3600

        # Test with direct use of send_file.
        with flask.send_file("static/index.html") as rv:
            assert rv.cache_control.max_age == 3600

        # Test with pathlib.Path.
        with app.send_static_file(FakePath("index.html")) as rv:
            assert rv.cache_control.max_age == 3600

        class StaticFileApp(flask.Flask):
            def get_send_file_max_age(self, filename):
                return 10

        app = StaticFileApp(__name__)

        with app.test_request_context():
            # Test with static file handler.
            with app.send_static_file("index.html") as rv:
                assert rv.cache_control.max_age == 10

            # Test with direct use of send_file.
            with flask.send_file("static/index.html") as rv:
                assert rv.cache_control.max_age == 10