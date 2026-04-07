def add_q(self, q_object, reuse_all=False):
        """
        A preprocessor for the internal _add_q(). Responsible for doing final
        join promotion.
        """
        # For join promotion this case is doing an AND for the added q_object
        # and existing conditions. So, any existing inner join forces the join
        # type to remain inner. Existing outer joins can however be demoted.
        # (Consider case where rel_a is LOUTER and rel_a__col=1 is added - if
        # rel_a doesn't produce any rows, then the whole condition must fail.
        # So, demotion is OK.
        existing_inner = {
            a for a in self.alias_map if self.alias_map[a].join_type == INNER
        }
        if reuse_all:
            can_reuse = set(self.alias_map)
        else:
            can_reuse = self.used_aliases
        clause, _ = self._add_q(q_object, can_reuse)
        if clause:
            self.where.add(clause, AND)
        self.demote_joins(existing_inner)