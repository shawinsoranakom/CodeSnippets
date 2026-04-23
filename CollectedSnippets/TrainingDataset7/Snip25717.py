def test_server_formatter_default_format(self):
        server_time = "2016-09-25 10:20:30"
        log_msg = "log message"
        logger = logging.getLogger("django.server")

        @contextmanager
        def patch_django_server_logger():
            old_stream = logger.handlers[0].stream
            new_stream = StringIO()
            logger.handlers[0].stream = new_stream
            yield new_stream
            logger.handlers[0].stream = old_stream

        with patch_django_server_logger() as logger_output:
            logger.info(log_msg, extra={"server_time": server_time})
            self.assertEqual(
                "[%s] %s\n" % (server_time, log_msg), logger_output.getvalue()
            )

        with patch_django_server_logger() as logger_output:
            logger.info(log_msg)
            self.assertRegex(
                logger_output.getvalue(), r"^\[[/:,\w\s\d]+\] %s\n" % log_msg
            )