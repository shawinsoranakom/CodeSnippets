def set_default_headers(self) -> None:
        if allow_cross_origin_requests():
            self.set_header("Access-Control-Allow-Origin", "*")