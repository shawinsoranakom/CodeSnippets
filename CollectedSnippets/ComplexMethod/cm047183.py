def log_request(self, code="-", size="-"):
        try:
            path = uri_to_iri(self.path)
            fragment = thread_local.rpc_model_method
            if fragment:
                path += '#' + fragment
            msg = f"{self.command} {path} {self.request_version}"
        except AttributeError:
            # path isn't set if the requestline was bad
            msg = self.requestline

        code = str(code)

        if code[0] == "1":  # 1xx - Informational
            msg = werkzeug.serving._ansi_style(msg, "bold")
        elif code == "200":  # 2xx - Success
            pass
        elif code == "304":  # 304 - Resource Not Modified
            msg = werkzeug.serving._ansi_style(msg, "cyan")
        elif code[0] == "3":  # 3xx - Redirection
            msg = werkzeug.serving._ansi_style(msg, "green")
        elif code == "404":  # 404 - Resource Not Found
            msg = werkzeug.serving._ansi_style(msg, "yellow")
        elif code[0] == "4":  # 4xx - Client Error
            msg = werkzeug.serving._ansi_style(msg, "bold", "red")
        else:  # 5xx, or any other response
            msg = werkzeug.serving._ansi_style(msg, "bold", "magenta")

        self.log("info", '"%s" %s %s', msg, code, size)