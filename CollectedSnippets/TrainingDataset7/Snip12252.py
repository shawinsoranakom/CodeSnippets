def resolve_expression(self, query, *args, **kwargs):
        clone = self.clone()
        # Subqueries need to use a different set of aliases than the outer
        # query.
        clone.bump_prefix(query)
        clone.subquery = True
        clone.where.resolve_expression(query, *args, **kwargs)
        # Resolve combined queries.
        if clone.combinator:
            clone.combined_queries = tuple(
                [
                    combined_query.resolve_expression(query, *args, **kwargs)
                    for combined_query in clone.combined_queries
                ]
            )
        for key, value in clone.annotations.items():
            resolved = value.resolve_expression(query, *args, **kwargs)
            if hasattr(resolved, "external_aliases"):
                resolved.external_aliases.update(clone.external_aliases)
            clone.annotations[key] = resolved
        # Outer query's aliases are considered external.
        for alias, table in query.alias_map.items():
            clone.external_aliases[alias] = (
                isinstance(table, Join)
                and table.join_field.related_model._meta.db_table != alias
            ) or (
                isinstance(table, BaseTable) and table.table_name != table.table_alias
            )
        return clone