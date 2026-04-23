def set_default_headers(self):
        # Avoid a circular import
        from streamlit.web.server import allow_cross_origin_requests

        if allow_cross_origin_requests():
            self.set_header("Access-Control-Allow-Origin", "*")