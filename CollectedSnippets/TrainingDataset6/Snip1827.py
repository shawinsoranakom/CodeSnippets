def make_authenticate_headers(self) -> dict[str, str]:
        if self.realm:
            return {"WWW-Authenticate": f'Basic realm="{self.realm}"'}
        return {"WWW-Authenticate": "Basic"}