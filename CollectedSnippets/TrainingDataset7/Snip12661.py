def get_default_prefix(cls):
        return cls.fk.remote_field.get_accessor_name(model=cls.model).replace("+", "")