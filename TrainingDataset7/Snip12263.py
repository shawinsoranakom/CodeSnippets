def build_filter(
        self,
        filter_expr,
        branch_negated=False,
        current_negated=False,
        can_reuse=None,
        allow_joins=True,
        split_subq=True,
        check_filterable=True,
        summarize=False,
        update_join_types=True,
    ):
        """
        Build a WhereNode for a single filter clause but don't add it
        to this Query. Query.add_q() will then add this filter to the where
        Node.

        The 'branch_negated' tells us if the current branch contains any
        negations. This will be used to determine if subqueries are needed.

        The 'current_negated' is used to determine if the current filter is
        negated or not and this will be used to determine if IS NULL filtering
        is needed.

        The difference between current_negated and branch_negated is that
        branch_negated is set on first negation, but current_negated is
        flipped for each negation.

        Note that add_filter will not do any negating itself, that is done
        upper in the code by add_q().

        The 'can_reuse' is a set of reusable joins for multijoins.

        The method will create a filter clause that can be added to the current
        query. However, if the filter isn't added to the query then the caller
        is responsible for unreffing the joins used.
        """
        if isinstance(filter_expr, dict):
            raise FieldError("Cannot parse keyword query as dict")
        if isinstance(filter_expr, Q):
            return self._add_q(
                filter_expr,
                branch_negated=branch_negated,
                current_negated=current_negated,
                used_aliases=can_reuse,
                allow_joins=allow_joins,
                split_subq=split_subq,
                check_filterable=check_filterable,
                summarize=summarize,
                update_join_types=update_join_types,
            )
        if hasattr(filter_expr, "resolve_expression"):
            if not getattr(filter_expr, "conditional", False):
                raise TypeError("Cannot filter against a non-conditional expression.")
            condition = filter_expr.resolve_expression(
                self, allow_joins=allow_joins, reuse=can_reuse, summarize=summarize
            )
            if not isinstance(condition, Lookup):
                condition = self.build_lookup(["exact"], condition, True)
            return WhereNode([condition], connector=AND), []
        arg, value = filter_expr
        if not arg:
            raise FieldError("Cannot parse keyword query %r" % arg)
        lookups, parts, reffed_expression = self.solve_lookup_type(arg, summarize)

        if check_filterable:
            self.check_filterable(reffed_expression)

        if not allow_joins and len(parts) > 1:
            raise FieldError("Joined field references are not permitted in this query")

        pre_joins = self.alias_refcount.copy()
        value = self.resolve_lookup_value(value, can_reuse, allow_joins, summarize)
        used_joins = {
            k for k, v in self.alias_refcount.items() if v > pre_joins.get(k, 0)
        }

        if check_filterable:
            self.check_filterable(value)

        if reffed_expression:
            condition = self.build_lookup(lookups, reffed_expression, value)
            return WhereNode([condition], connector=AND), []

        opts = self.get_meta()
        alias = self.get_initial_alias()
        allow_many = not branch_negated or not split_subq

        try:
            join_info = self.setup_joins(
                parts,
                opts,
                alias,
                can_reuse=can_reuse,
                allow_many=allow_many,
            )

            # Prevent iterator from being consumed by check_related_objects()
            if isinstance(value, Iterator):
                value = list(value)
            self.check_related_objects(join_info.final_field, value, join_info.opts)

            # split_exclude() needs to know which joins were generated for the
            # lookup parts
            self._lookup_joins = join_info.joins
        except MultiJoin as e:
            return self.split_exclude(filter_expr, can_reuse, e.names_with_path)

        # Update used_joins before trimming since they are reused to determine
        # which joins could be later promoted to INNER.
        used_joins.update(join_info.joins)
        targets, alias, join_list = self.trim_joins(
            join_info.targets, join_info.joins, join_info.path
        )
        if can_reuse is not None:
            can_reuse.update(join_list)

        if join_info.final_field.is_relation:
            if len(targets) == 1:
                col = self._get_col(targets[0], join_info.final_field, alias)
            else:
                col = ColPairs(alias, targets, join_info.targets, join_info.final_field)
        else:
            col = self._get_col(targets[0], join_info.final_field, alias)

        condition = self.build_lookup(lookups, col, value)
        lookup_type = condition.lookup_name
        clause = WhereNode([condition], connector=AND)

        require_outer = (
            lookup_type == "isnull" and condition.rhs is True and not current_negated
        )
        if (
            current_negated
            and (lookup_type != "isnull" or condition.rhs is False)
            and condition.rhs is not None
        ):
            require_outer = True
            if lookup_type != "isnull":
                # The condition added here will be SQL like this:
                # NOT (col IS NOT NULL), where the first NOT is added in
                # upper layers of code. The reason for addition is that if col
                # is null, then col != someval will result in SQL "unknown"
                # which isn't the same as in Python. The Python None handling
                # is wanted, and it can be gotten by
                # (col IS NULL OR col != someval)
                #   <=>
                # NOT (col IS NOT NULL AND col = someval).
                if (
                    self.is_nullable(targets[0])
                    or self.alias_map[join_list[-1]].join_type == LOUTER
                ):
                    lookup_class = targets[0].get_lookup("isnull")
                    col = self._get_col(targets[0], join_info.targets[0], alias)
                    # Use OR + IS NULL when RHS `in` values include None.
                    if (
                        lookup_type == "in"
                        # Check containers (not strings or bytes).
                        and isinstance(condition.rhs, Iterable)
                        and not isinstance(condition.rhs, (str, bytes))
                        and any(v is None for v in condition.rhs)
                    ):
                        clause.add(lookup_class(col, True), OR)
                    else:
                        clause.add(lookup_class(col, False), AND)
                # If someval is a nullable column, someval IS NOT NULL is
                # added.
                if isinstance(value, Col) and self.is_nullable(value.target):
                    lookup_class = value.target.get_lookup("isnull")
                    clause.add(lookup_class(value, False), AND)
        return clause, used_joins if not require_outer else ()