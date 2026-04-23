def __init__(self, field):
        internal_type = getattr(field, "target_field", field).get_internal_type()
        self.db_type = self.types.get(internal_type, str)
        self.bound_param = None