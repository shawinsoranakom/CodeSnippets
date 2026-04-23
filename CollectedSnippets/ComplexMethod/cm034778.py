def validateCredentials(self, data):
        if not data or not isinstance(data, dict):
            raise ValueError("Invalid credentials format")
        for field in ["access_token", "refresh_token", "token_type"]:
            if field not in data or not isinstance(data[field], str):
                raise ValueError(f"Invalid credentials: missing {field}")
        if "expiry_date" not in data or not isinstance(data["expiry_date"], (int, float)):
            raise ValueError("Invalid credentials: missing expiry_date")
        return data