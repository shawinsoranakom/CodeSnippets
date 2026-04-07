def test_logs_with_custom_logger(self):
        handler = logging.StreamHandler(log_stream := StringIO())
        handler.setFormatter(logging.Formatter("%(levelname)s:%(name)s:%(message)s"))

        custom_logger = logging.getLogger("my.custom.logger")
        custom_logger.setLevel(logging.DEBUG)
        custom_logger.addHandler(handler)
        self.addCleanup(custom_logger.removeHandler, handler)

        response = HttpResponse(status=404)
        log_response(
            msg := "Handled by custom logger",
            response=response,
            request=self.request,
            logger=custom_logger,
        )

        self.assertEqual(
            f"WARNING:my.custom.logger:{msg}", log_stream.getvalue().strip()
        )