def test_control_chars_escaped(self):
        self.assertLogsRequest(
            url="/%1B[1;31mNOW IN RED!!!1B[0m/",
            level="WARNING",
            status_code=404,
            msg=r"Not Found: /\x1b[1;31mNOW IN RED!!!1B[0m/",
        )