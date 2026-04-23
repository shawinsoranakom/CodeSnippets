def create_model_instance(self, data):
        obj = super().create_model_instance(data)

        try:
            account_id = int(data.get("_auth_user_id"))
        except (ValueError, TypeError):
            account_id = None
        obj.account_id = account_id

        return obj