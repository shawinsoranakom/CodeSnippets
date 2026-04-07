def find_ordering_name(
        self, name, opts, alias=None, default_order="ASC", already_seen=None
    ):
        """
        Return the table alias (the name might be ambiguous, the alias will
        not be) and column name for ordering by the given 'name' parameter.
        The 'name' is of the form 'field1__field2__...__fieldN'.
        """
        name, order = get_order_dir(name, default_order)
        descending = order == "DESC"
        pieces = name.split(LOOKUP_SEP)
        (
            field,
            targets,
            alias,
            joins,
            path,
            opts,
            transform_function,
        ) = self._setup_joins(pieces, opts, alias)

        # If we get to this point and the field is a relation to another model,
        # append the default ordering for that model unless it is the pk
        # shortcut or the attribute name of the field that is specified or
        # there are transforms to process.
        if (
            field.is_relation
            and opts.ordering
            and getattr(field, "attname", None) != pieces[-1]
            and name != "pk"
            and not getattr(transform_function, "has_transforms", False)
        ):
            # Firstly, avoid infinite loops.
            already_seen = already_seen or set()
            join_tuple = tuple(
                getattr(self.query.alias_map[j], "join_cols", None) for j in joins
            )
            if join_tuple in already_seen:
                raise FieldError("Infinite loop caused by ordering.")
            already_seen.add(join_tuple)

            results = []
            for item in opts.ordering:
                if hasattr(item, "resolve_expression") and not isinstance(
                    item, OrderBy
                ):
                    item = item.desc() if descending else item.asc()
                if isinstance(item, OrderBy):
                    results.append(
                        (item.prefix_references(f"{name}{LOOKUP_SEP}"), False)
                    )
                    continue
                results.extend(
                    (expr.prefix_references(f"{name}{LOOKUP_SEP}"), is_ref)
                    for expr, is_ref in self.find_ordering_name(
                        item, opts, alias, order, already_seen
                    )
                )
            return results
        targets, alias, _ = self.query.trim_joins(targets, joins, path)
        return [
            (OrderBy(transform_function(t, alias), descending=descending), False)
            for t in targets
        ]