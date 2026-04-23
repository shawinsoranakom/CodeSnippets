def secure_request_kwargs(self):
        return {"wsgi.url_scheme": "https"}