def __init__(self, *args, **kwargs):
        if (
            not args
            or not all(isinstance(field, str) for field in args)
            or len(set(args)) != len(args)
        ):
            raise ValueError("CompositePrimaryKey args must be unique strings.")
        if len(args) == 1:
            raise ValueError("CompositePrimaryKey must include at least two fields.")
        if kwargs.get("default", NOT_PROVIDED) is not NOT_PROVIDED:
            raise ValueError("CompositePrimaryKey cannot have a default.")
        if kwargs.get("db_default", NOT_PROVIDED) is not NOT_PROVIDED:
            raise ValueError("CompositePrimaryKey cannot have a database default.")
        if kwargs.get("db_column", None) is not None:
            raise ValueError("CompositePrimaryKey cannot have a db_column.")
        if kwargs.setdefault("editable", False):
            raise ValueError("CompositePrimaryKey cannot be editable.")
        if not kwargs.setdefault("primary_key", True):
            raise ValueError("CompositePrimaryKey must be a primary key.")
        if not kwargs.setdefault("blank", True):
            raise ValueError("CompositePrimaryKey must be blank.")

        self.field_names = args
        super().__init__(**kwargs)