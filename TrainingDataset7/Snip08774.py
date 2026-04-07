def get_meta(
        self,
        table_name,
        constraints,
        column_to_field_name,
        is_view,
        is_partition,
        comment,
    ):
        """
        Return a sequence comprising the lines of code necessary
        to construct the inner Meta class for the model corresponding
        to the given database table name.
        """
        unique_together = []
        has_unsupported_constraint = False
        for params in constraints.values():
            if params["unique"]:
                columns = params["columns"]
                if None in columns:
                    has_unsupported_constraint = True
                columns = [
                    x for x in columns if x is not None and x in column_to_field_name
                ]
                if len(columns) > 1 and not params["primary_key"]:
                    unique_together.append(
                        str(tuple(column_to_field_name[c] for c in columns))
                    )
        if is_view:
            managed_comment = "  # Created from a view. Don't remove."
        elif is_partition:
            managed_comment = "  # Created from a partition. Don't remove."
        else:
            managed_comment = ""
        meta = [""]
        if has_unsupported_constraint:
            meta.append("    # A unique constraint could not be introspected.")
        meta += [
            "    class Meta:",
            "        managed = False%s" % managed_comment,
            "        db_table = %r" % table_name,
        ]
        if unique_together:
            tup = "(" + ", ".join(unique_together) + ",)"
            meta += ["        unique_together = %s" % tup]
        if comment:
            meta += [f"        db_table_comment = {comment!r}"]
        return meta