def test_server_formatter_styles(self):
        color_style = color.make_style("")
        formatter = ServerFormatter()
        formatter.style = color_style
        log_msg = "log message"
        status_code_styles = [
            (200, "HTTP_SUCCESS"),
            (100, "HTTP_INFO"),
            (304, "HTTP_NOT_MODIFIED"),
            (300, "HTTP_REDIRECT"),
            (404, "HTTP_NOT_FOUND"),
            (400, "HTTP_BAD_REQUEST"),
            (500, "HTTP_SERVER_ERROR"),
        ]
        for status_code, style in status_code_styles:
            record = logging.makeLogRecord({"msg": log_msg, "status_code": status_code})
            self.assertEqual(
                formatter.format(record), getattr(color_style, style)(log_msg)
            )
        record = logging.makeLogRecord({"msg": log_msg})
        self.assertEqual(formatter.format(record), log_msg)