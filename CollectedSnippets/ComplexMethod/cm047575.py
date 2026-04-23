def fetch(self, field_names: Collection[str] | None = None) -> None:
        """ Make sure the given fields are in memory for the records in ``self``,
        by fetching what is necessary from the database.  Non-stored fields are
        mostly ignored, except for their stored dependencies. This method should
        be called to optimize code.

        :param field_names: a collection of field names to fetch, or ``None`` for
            all accessible fields marked with ``prefetch=True``
        :raise AccessError: if user is not allowed to access requested information

        This method is implemented thanks to methods :meth:`_search` and
        :meth:`_fetch_query`, and should not be overridden.
        """
        self = self._origin  # noqa: PLW0642 filtered out new records
        if not self or not (field_names is None or field_names):
            return

        fields_to_fetch = self._determine_fields_to_fetch(field_names, ignore_when_in_cache=True)

        # first determine a query that satisfies the domain and access rules
        if any(field.column_type for field in fields_to_fetch):
            query = self._search([('id', 'in', self.ids)], active_test=False)
        else:
            try:
                self.check_access('read')
            except MissingError:
                # Method fetch() should never raise a MissingError, but method
                # check_access() can, because it must read fields on self.
                # So we restrict 'self' to existing records (to avoid an extra
                # exists() at the end of the method).
                self = self.exists()
                self.check_access('read')
            if not fields_to_fetch:
                return
            query = self._as_query(ordered=False)

        # fetch the fields
        fetched = self._fetch_query(query, fields_to_fetch)

        # possibly raise exception for the records that could not be read
        if fetched != self:
            forbidden = (self - fetched).exists()
            if forbidden:
                raise self.env['ir.rule']._make_access_error('read', forbidden)