def get_db_prep_value(self, value, connection, *args, **kwargs):
        if value is None:
            return None
        return connection.ops.Adapter(
            super().get_db_prep_value(value, connection, *args, **kwargs),
            **(
                {"geography": True}
                if self.geography and connection.features.supports_geography
                else {}
            ),
        )