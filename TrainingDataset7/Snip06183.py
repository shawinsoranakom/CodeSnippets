def changed_data(self):
        data = super().changed_data
        if "set_usable_password" in data or "password1" in data and "password2" in data:
            return ["password"]
        return []