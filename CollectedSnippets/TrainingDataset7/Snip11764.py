def set_name_with_model(self, model):
        """
        Generate a unique name for the index.

        The name is divided into 3 parts - table name (12 chars), field name
        (8 chars) and unique hash + suffix (10 chars). Each part is made to
        fit its size by truncating the excess length.
        """
        _, table_name = split_identifier(model._meta.db_table)
        column_names = [
            model._meta.get_field(field_name).column
            for field_name, order in self.fields_orders
        ]
        column_names_with_order = [
            (("-%s" if order else "%s") % column_name)
            for column_name, (field_name, order) in zip(
                column_names, self.fields_orders
            )
        ]
        # The length of the parts of the name is based on the default max
        # length of 30 characters.
        hash_data = [table_name, *column_names_with_order, self.suffix]
        self.name = "%s_%s_%s" % (
            table_name[:11],
            column_names[0][:7],
            "%s_%s" % (names_digest(*hash_data, length=6), self.suffix),
        )
        if len(self.name) > self.max_name_length:
            raise ValueError(
                "Index too long for multiple database support. Is self.suffix "
                "longer than 3 characters?"
            )
        if self.name[0] == "_" or self.name[0].isdigit():
            self.name = "D%s" % self.name[1:]