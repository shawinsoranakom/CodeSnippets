def modify_insert_params(self, placeholder, params):
        """Drop out insert parameters for NULL placeholder. Needed for Oracle
        Spatial backend due to #10888.
        """
        if placeholder == "NULL":
            return []
        return super().modify_insert_params(placeholder, params)