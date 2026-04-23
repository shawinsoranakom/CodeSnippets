def set_default_headers(self) -> None:
        if streamlit.web.server.routes.allow_cross_origin_requests():
            self.set_header("Access-Control-Allow-Origin", "*")