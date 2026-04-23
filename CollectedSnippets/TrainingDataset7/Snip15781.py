def test_zero_ip_addr(self):
        self.cmd.addr = "0"
        self.cmd._raw_ipv6 = False
        self.cmd.on_bind("8000")
        self.assertIn(
            "Starting WSGI development server at http://0.0.0.0:8000/",
            self.output.getvalue(),
        )
        docs_version = get_docs_version()
        self.assertIn(
            "WARNING: This is a development server. Do not use it in a "
            "production setting. Use a production WSGI or ASGI server instead."
            "\nFor more information on production servers see: "
            f"https://docs.djangoproject.com/en/{docs_version}/howto/"
            "deployment/",
            self.output.getvalue(),
        )