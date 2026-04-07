def process_rhs(self, qn, connection):
        if not connection.features.has_native_uuid_field:
            from django.db.models.functions import Replace

            if self.rhs_is_direct_value():
                self.rhs = Value(self.rhs)
            self.rhs = Replace(
                self.rhs, Value("-"), Value(""), output_field=CharField()
            )
        rhs, params = super().process_rhs(qn, connection)
        return rhs, params