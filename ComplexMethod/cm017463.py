def pre_sql_setup(self):
        """
        If the update depends on results from other tables, munge the "where"
        conditions to match the format required for (portable) SQL updates.

        If multiple updates are required, pull out the id values to update at
        this point so that they don't change as a result of the progressive
        updates.
        """
        refcounts_before = self.query.alias_refcount.copy()
        # Ensure base table is in the query
        self.query.get_initial_alias()
        count = self.query.count_active_tables()
        if not self.query.related_updates and count == 1:
            return
        query = self.query.chain(klass=Query)
        query.select_related = False
        query.clear_ordering(force=True)
        query.extra = {}
        query.select = []
        meta = query.get_meta()
        fields = [meta.pk.name]
        related_ids_index = []
        for related in self.query.related_updates:
            if all(
                path.join_field.primary_key for path in meta.get_path_to_parent(related)
            ):
                # If a primary key chain exists to the targeted related update,
                # then the meta.pk value can be used for it.
                related_ids_index.append((related, 0))
            else:
                # This branch will only be reached when updating a field of an
                # ancestor that is not part of the primary key chain of a MTI
                # tree.
                related_ids_index.append((related, len(fields)))
                fields.append(related._meta.pk.name)
        query.add_fields(fields)
        super().pre_sql_setup()

        is_composite_pk = meta.is_composite_pk
        must_pre_select = (
            count > 1 and not self.connection.features.update_can_self_select
        )

        # Now we adjust the current query: reset the where clause and get rid
        # of all the tables we don't need (since they're in the sub-select).
        self.query.clear_where()
        if self.query.related_updates or must_pre_select:
            # Either we're using the idents in multiple update queries (so
            # don't want them to change), or the db backend doesn't support
            # selecting from the updating table (e.g. MySQL).
            idents = []
            related_ids = collections.defaultdict(list)
            for rows in query.get_compiler(self.using).execute_sql(MULTI):
                pks = [row if is_composite_pk else row[0] for row in rows]
                idents.extend(pks)
                for parent, index in related_ids_index:
                    related_ids[parent].extend(r[index] for r in rows)
            self.query.add_filter("pk__in", idents)
            self.query.related_ids = related_ids
        else:
            # The fast path. Filters and updates in one query.
            self.query.add_filter("pk__in", query)
        self.query.reset_refcounts(refcounts_before)