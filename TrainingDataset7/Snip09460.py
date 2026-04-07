def __init__(
        self,
        from_table,
        from_columns,
        to_table,
        to_columns,
        suffix_template,
        create_fk_name,
    ):
        self.to_reference = TableColumns(to_table, to_columns)
        self.suffix_template = suffix_template
        self.create_fk_name = create_fk_name
        super().__init__(
            from_table,
            from_columns,
        )