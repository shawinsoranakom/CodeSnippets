def __init__(self, *, expression, output_field, db_persist, **kwargs):
        if kwargs.setdefault("editable", False):
            raise ValueError("GeneratedField cannot be editable.")
        if not kwargs.setdefault("blank", True):
            raise ValueError("GeneratedField must be blank.")
        if kwargs.get("default", NOT_PROVIDED) is not NOT_PROVIDED:
            raise ValueError("GeneratedField cannot have a default.")
        if kwargs.get("db_default", NOT_PROVIDED) is not NOT_PROVIDED:
            raise ValueError("GeneratedField cannot have a database default.")
        if db_persist not in (True, False):
            raise ValueError("GeneratedField.db_persist must be True or False.")

        self.expression = expression
        self.output_field = output_field
        self.db_persist = db_persist
        self.has_null_arg = "null" in kwargs
        super().__init__(**kwargs)