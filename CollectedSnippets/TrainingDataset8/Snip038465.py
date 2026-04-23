def set_default_headers(self):
        self.set_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.set_header("Access-Control-Allow-Headers", "Content-Type")
        if config.get_option("server.enableXsrfProtection"):
            self.set_header(
                "Access-Control-Allow-Origin",
                server_util.get_url(config.get_option("browser.serverAddress")),
            )
            self.set_header("Access-Control-Allow-Headers", "X-Xsrftoken, Content-Type")
            self.set_header("Vary", "Origin")
            self.set_header("Access-Control-Allow-Credentials", "true")
        elif routes.allow_cross_origin_requests():
            self.set_header("Access-Control-Allow-Origin", "*")