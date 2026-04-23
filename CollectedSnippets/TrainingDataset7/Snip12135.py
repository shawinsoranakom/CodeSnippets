def _order_by_pairs(self):
        if self.query.extra_order_by:
            ordering = self.query.extra_order_by
        elif not self.query.default_ordering:
            ordering = self.query.order_by
        elif self.query.order_by:
            ordering = self.query.order_by
        elif (meta := self.query.get_meta()) and meta.ordering:
            ordering = meta.ordering
            self._meta_ordering = ordering
        else:
            ordering = []
        if self.query.standard_ordering:
            default_order, _ = ORDER_DIR["ASC"]
        else:
            default_order, _ = ORDER_DIR["DESC"]

        selected_exprs = {}
        # Avoid computing `selected_exprs` if there is no `ordering` as it's
        # relatively expensive.
        if ordering and (select := self.select):
            for ordinal, (expr, _, alias) in enumerate(select, start=1):
                pos_expr = PositionRef(ordinal, alias, expr)
                if alias:
                    selected_exprs[alias] = pos_expr
                selected_exprs[expr] = pos_expr

        for field in ordering:
            if hasattr(field, "resolve_expression"):
                if isinstance(field, Value):
                    # output_field must be resolved for constants.
                    field = Cast(field, field.output_field)
                if not isinstance(field, OrderBy):
                    field = field.asc()
                if not self.query.standard_ordering:
                    field = field.copy()
                    field.reverse_ordering()
                select_ref = selected_exprs.get(field.expression)
                if select_ref or (
                    isinstance(field.expression, F)
                    and (select_ref := selected_exprs.get(field.expression.name))
                ):
                    # Emulation of NULLS (FIRST|LAST) cannot be combined with
                    # the usage of ordering by position.
                    if (
                        field.nulls_first is None and field.nulls_last is None
                    ) or self.connection.features.supports_order_by_nulls_modifier:
                        field = field.copy()
                        field.expression = select_ref
                    # Alias collisions are not possible when dealing with
                    # combined queries so fallback to it if emulation of NULLS
                    # handling is required.
                    elif self.query.combinator:
                        field = field.copy()
                        field.expression = Ref(select_ref.refs, select_ref.source)
                yield field, select_ref is not None
                continue
            if field == "?":  # random
                yield OrderBy(Random()), False
                continue

            col, order = get_order_dir(field, default_order)
            descending = order == "DESC"

            if select_ref := selected_exprs.get(col):
                # Reference to expression in SELECT clause
                yield (
                    OrderBy(
                        select_ref,
                        descending=descending,
                    ),
                    True,
                )
                continue

            if expr := self.query.annotations.get(col):
                ref = col
                transforms = []
            else:
                ref, *transforms = col.split(LOOKUP_SEP)
                expr = self.query.annotations.get(ref)
            if expr:
                if self.query.combinator and self.select:
                    if transforms:
                        raise NotImplementedError(
                            "Ordering combined queries by transforms is not "
                            "implemented."
                        )
                    # Don't use the resolved annotation because other
                    # combined queries might define it differently.
                    expr = F(ref)
                if transforms:
                    for name in transforms:
                        expr = self.query.try_transform(expr, name)
                if isinstance(expr, Value):
                    # output_field must be resolved for constants.
                    expr = Cast(expr, expr.output_field)
                yield OrderBy(expr, descending=descending), False
                continue

            if "." in field and field in self.query.extra_order_by:
                # This came in through an extra(order_by=...) addition. Pass it
                # on verbatim.
                table, col = col.split(".", 1)
                yield (
                    OrderBy(
                        RawSQL("%s.%s" % (self.quote_name(table), col), []),
                        descending=descending,
                    ),
                    False,
                )
                continue

            if self.query.extra and col in self.query.extra:
                if col in self.query.extra_select:
                    yield (
                        OrderBy(
                            Ref(col, RawSQL(*self.query.extra[col])),
                            descending=descending,
                        ),
                        True,
                    )
                else:
                    yield (
                        OrderBy(RawSQL(*self.query.extra[col]), descending=descending),
                        False,
                    )
            else:
                if self.query.combinator and self.select:
                    # Don't use the first model's field because other
                    # combinated queries might define it differently.
                    yield OrderBy(F(col), descending=descending), False
                else:
                    # 'col' is of the form 'field' or 'field1__field2' or
                    # '-field1__field2__field', etc.
                    yield from self.find_ordering_name(
                        field,
                        self.query.get_meta(),
                        default_order=default_order,
                    )