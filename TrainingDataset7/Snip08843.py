def on_bind(self, server_port):
        quit_command = "CTRL-BREAK" if sys.platform == "win32" else "CONTROL-C"

        if self._raw_ipv6:
            addr = f"[{self.addr}]"
        elif self.addr == "0":
            addr = "0.0.0.0"
        else:
            addr = self.addr

        now = datetime.now().strftime("%B %d, %Y - %X")
        version = self.get_version()
        print(
            f"{now}\n"
            f"Django version {version}, using settings {settings.SETTINGS_MODULE!r}\n"
            f"Starting WSGI development server at {self.protocol}://{addr}"
            f":{server_port}/\n"
            f"Quit the server with {quit_command}.",
            file=self.stdout,
        )
        docs_version = get_docs_version()
        if os.environ.get("DJANGO_RUNSERVER_HIDE_WARNING") != "true":
            self.stdout.write(
                self.style.WARNING(
                    "WARNING: This is a development server. Do not use it in a "
                    "production setting. Use a production WSGI or ASGI server "
                    "instead.\nFor more information on production servers see: "
                    f"https://docs.djangoproject.com/en/{docs_version}/howto/"
                    "deployment/"
                )
            )