def _headers(self, auth_kind: Optional[str], extra: Optional[Dict[str, str]]) -> Dict[str, str]:
        headers = {}
        if auth_kind == "api" and self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        elif auth_kind == "web" and self.login_token:
            headers["Authorization"] = self.login_token
        elif auth_kind == "admin" and self.login_token:
            headers["Authorization"] = self.login_token
        else:
            pass
        if extra:
            headers.update(extra)
        return headers