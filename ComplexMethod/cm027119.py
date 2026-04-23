def _generate_filter_for_columns(
        self, columns: Iterable[Column], encoder: Callable[[Any], Any]
    ) -> ColumnElement:
        """Generate a filter from pre-computed sets and pattern lists.

        This must match exactly how homeassistant.helpers.entityfilter works.
        """
        i_domains = _domain_matcher(self._included_domains, columns, encoder)
        i_entities = _entity_matcher(self._included_entities, columns, encoder)
        i_entity_globs = _globs_to_like(self._included_entity_globs, columns, encoder)
        includes = [i_domains, i_entities, i_entity_globs]

        e_domains = _domain_matcher(self._excluded_domains, columns, encoder)
        e_entities = _entity_matcher(self._excluded_entities, columns, encoder)
        e_entity_globs = _globs_to_like(self._excluded_entity_globs, columns, encoder)
        excludes = [e_domains, e_entities, e_entity_globs]

        have_exclude = self._have_exclude
        have_include = self._have_include

        # Case 1 - No filter
        # - All entities included
        if not have_include and not have_exclude:
            raise RuntimeError(
                "No filter configuration provided, check has_config before calling this method."
            )

        # Case 2 - Only includes
        # - Entity listed in entities include: include
        # - Otherwise, entity matches domain include: include
        # - Otherwise, entity matches glob include: include
        # - Otherwise: exclude
        if have_include and not have_exclude:
            return or_(*includes).self_group()

        # Case 3 - Only excludes
        # - Entity listed in exclude: exclude
        # - Otherwise, entity matches domain exclude: exclude
        # - Otherwise, entity matches glob exclude: exclude
        # - Otherwise: include
        if not have_include and have_exclude:
            return not_(or_(*excludes).self_group())

        # Case 4 - Domain and/or glob includes (may also have excludes)
        # - Entity listed in entities include: include
        # - Otherwise, entity listed in entities exclude: exclude
        # - Otherwise, entity matches glob include: include
        # - Otherwise, entity matches glob exclude: exclude
        # - Otherwise, entity matches domain include: include
        # - Otherwise: exclude
        if self._included_domains or self._included_entity_globs:
            return or_(
                i_entities,
                (~e_entities & (i_entity_globs | (~e_entity_globs & i_domains))),
            ).self_group()

        # Case 5 - Domain and/or glob excludes (no domain and/or glob includes)
        # - Entity listed in entities include: include
        # - Otherwise, entity listed in exclude: exclude
        # - Otherwise, entity matches glob exclude: exclude
        # - Otherwise, entity matches domain exclude: exclude
        # - Otherwise: include
        if self._excluded_domains or self._excluded_entity_globs:
            return (not_(or_(*excludes)) | i_entities).self_group()

        # Case 6 - No Domain and/or glob includes or excludes
        # - Entity listed in entities include: include
        # - Otherwise: exclude
        return i_entities