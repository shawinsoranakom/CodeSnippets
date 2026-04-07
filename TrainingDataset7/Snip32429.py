def test_404_response(self):
        command = runserver.Command()
        handler = command.get_handler(use_static_handler=True, insecure_serving=True)
        missing_static_file = os.path.join(settings.STATIC_URL, "unknown.css")
        req = RequestFactory().get(missing_static_file)
        with override_settings(DEBUG=False):
            response = handler.get_response(req)
            self.assertEqual(response.status_code, 404)
        with override_settings(DEBUG=True):
            response = handler.get_response(req)
            self.assertEqual(response.status_code, 404)