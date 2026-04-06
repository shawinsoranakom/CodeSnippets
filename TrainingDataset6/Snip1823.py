def make_authenticate_headers(self) -> dict[str, str]:
        return {"WWW-Authenticate": f"{self.model.scheme.title()}"}