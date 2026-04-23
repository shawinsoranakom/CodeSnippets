def log_message(self, format, *args):
        if args[1][0] == "4" and args[0].startswith("\x16\x03"):
            # 0x16 = Handshake, 0x03 = SSL 3.0 or TLS 1.x
            format = (
                "You're accessing the development server over HTTPS, but it only "
                "supports HTTP."
            )
            status_code = 500
            args = ()
        elif args[1].isdigit() and len(args[1]) == 3:
            status_code = int(args[1])
        else:
            status_code = None

        log_message(
            logger,
            format,
            *args,
            request=self.request,
            status_code=status_code,
            server_time=self.log_date_time_string(),
        )