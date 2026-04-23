def get_select(self, with_col_aliases=False):
        """
        Return three values:
        - a list of 3-tuples of (expression, (sql, params), alias)
        - a klass_info structure,
        - a dictionary of annotations

        The (sql, params) is what the expression will produce, and alias is the
        "AS alias" for the column (possibly None).

        The klass_info structure contains the following information:
        - The base model of the query.
        - Which columns for that model are present in the query (by
          position of the select clause).
        - related_klass_infos: [f, klass_info] to descent into

        The annotations is a dictionary of {'attname': column position} values.
        """
        select = []
        klass_info = None
        annotations = {}
        assert not (self.query.select and self.query.default_cols)
        select_mask = self.query.get_select_mask()
        if self.query.default_cols:
            cols = self.get_default_columns(select_mask)
        else:
            # self.query.select is a special case. These columns never go to
            # any model.
            cols = self.query.select
        selected = []
        select_fields = None
        if self.query.selected is None:
            selected = [
                *(
                    (alias, RawSQL(*args))
                    for alias, args in self.query.extra_select.items()
                ),
                *((None, col) for col in cols),
                *self.query.annotation_select.items(),
            ]
            select_fields = list(
                range(
                    len(self.query.extra_select),
                    len(self.query.extra_select) + len(cols),
                )
            )
        else:
            select_fields = []
            for index, (alias, expression) in enumerate(self.query.selected.items()):
                # Reference to an annotation.
                if isinstance(expression, str):
                    expression = self.query.annotations[expression]
                # Reference to a column.
                elif isinstance(expression, int):
                    select_fields.append(index)
                    expression = cols[expression]
                # ColPairs cannot be aliased.
                if isinstance(expression, ColPairs):
                    alias = None
                selected.append((alias, expression))
        if select_fields:
            klass_info = {"model": self.query.model, "select_fields": select_fields}

        for select_idx, (alias, expression) in enumerate(selected):
            if alias:
                annotations[alias] = select_idx
            select.append((expression, alias))

        if self.query.select_related:
            related_klass_infos = self.get_related_selections(select, select_mask)
            klass_info["related_klass_infos"] = related_klass_infos

            self.get_select_from_parent(klass_info)

        ret = []
        col_idx = 1
        for col, alias in select:
            try:
                sql, params = self.compile(col)
            except EmptyResultSet:
                empty_result_set_value = getattr(
                    col, "empty_result_set_value", NotImplemented
                )
                if empty_result_set_value is NotImplemented:
                    # Select a predicate that's always False.
                    sql, params = "0", ()
                else:
                    sql, params = self.compile(Value(empty_result_set_value))
            except FullResultSet:
                sql, params = self.compile(Value(True))
            else:
                sql, params = col.select_format(self, sql, params)
            if alias is None and with_col_aliases:
                alias = f"col{col_idx}"
                col_idx += 1
            ret.append((col, (sql, params), alias))
        return ret, klass_info, annotations