def _search(
        self,
        domain: DomainType,
        offset: int = 0,
        limit: int | None = None,
        order: str | None = None,
        *,
        active_test: bool = True,
        bypass_access: bool = False,
    ) -> Query:
        """
        Private implementation of search() method.

        No default order is applied when the method is invoked without parameter ``order``.

        :return: a :class:`Query` object that represents the matching records

        This method may be overridden to modify the domain being searched, or to
        do some post-filtering of the resulting query object. Be careful with
        the latter option, though, as it might hurt performance. Indeed, by
        default the returned query object is not actually executed, and it can
        be injected as a value in a domain in order to generate sub-queries.

        The `active_test` flag specifies whether to filter only active records.
        The `bypass_access` controls whether or not permissions should be
        checked on the model and record rules should be applied.
        """
        check_access = not (self.env.su or bypass_access)
        if check_access:
            self.browse().check_access('read')

        domain = Domain(domain)
        # inactive records unless they were explicitly asked for
        if (
            self._active_name
            and active_test
            and self.env.context.get('active_test', True)
            and not any(leaf.field_expr == self._active_name for leaf in domain.iter_conditions())
        ):
            domain &= Domain(self._active_name, '=', True)

        # build the query
        domain = domain.optimize_full(self)
        if domain.is_false():
            return self.browse()._as_query()
        query = Query(self.env, self._table, self._table_sql)
        if not domain.is_true():
            query.add_where(domain._to_sql(self, self._table, query))

        # security access domain
        if check_access:
            self_sudo = self.sudo().with_context(active_test=False)
            sec_domain = self.env['ir.rule']._compute_domain(self._name, 'read')
            sec_domain = sec_domain.optimize_full(self_sudo)
            if sec_domain.is_false():
                return self.browse()._as_query()
            if not sec_domain.is_true():
                query.add_where(sec_domain._to_sql(self_sudo, self._table, query))

        # add order and limits
        if order:
            query.order = self._order_to_sql(order, query)

        # In RPC, None is not available; False is used instead to mean "no limit"
        # Note: True is kept for backward-compatibility (treated as 1)
        if limit is not None and limit is not False:
            query.limit = limit
        if offset is not None:
            query.offset = offset

        return query