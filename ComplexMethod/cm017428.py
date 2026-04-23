def join(self, join, reuse=None):
        """
        Return an alias for the 'join', either reusing an existing alias for
        that join or creating a new one. 'join' is either a base_table_class or
        join_class.

        The 'reuse' parameter can be either None which means all joins are
        reusable, or it can be a set containing the aliases that can be reused.

        A join is always created as LOUTER if the lhs alias is LOUTER to make
        sure chains like t1 LOUTER t2 INNER t3 aren't generated. All new
        joins are created as LOUTER if the join is nullable.
        """
        reuse_aliases = [
            a
            for a, j in self.alias_map.items()
            if (reuse is None or a in reuse) and j == join
        ]
        if reuse_aliases:
            if join.table_alias in reuse_aliases:
                reuse_alias = join.table_alias
            else:
                # Reuse the most recent alias of the joined table
                # (a many-to-many relation may be joined multiple times).
                reuse_alias = reuse_aliases[-1]
            self.ref_alias(reuse_alias)
            return reuse_alias

        # No reuse is possible, so we need a new alias.
        alias, _ = self.table_alias(
            join.table_name, create=True, filtered_relation=join.filtered_relation
        )
        if join.join_type:
            if self.alias_map[join.parent_alias].join_type == LOUTER or join.nullable:
                join_type = LOUTER
            else:
                join_type = INNER
            join.join_type = join_type
        join.table_alias = alias
        self.alias_map[alias] = join
        if filtered_relation := join.filtered_relation:
            resolve_reuse = reuse
            if resolve_reuse is not None:
                resolve_reuse = set(reuse) | {alias}
            joins_len = len(self.alias_map)
            join.filtered_relation = filtered_relation.resolve_expression(
                self, reuse=resolve_reuse
            )
            # Some joins were during expression resolving, they must be present
            # before the one we just added.
            if joins_len < len(self.alias_map):
                self.alias_map[alias] = self.alias_map.pop(alias)
        return alias