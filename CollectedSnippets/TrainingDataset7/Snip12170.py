def as_sql(self):
        """
        Create the SQL for this query. Return the SQL string and list of
        parameters.
        """
        if self.single_alias and (
            self.connection.features.delete_can_self_reference_subquery
            or not self.contains_self_reference_subquery
        ):
            return self._as_sql(self.query)
        innerq = self.query.clone()
        innerq.__class__ = Query
        innerq.clear_select_clause()
        pk = self.query.model._meta.pk
        innerq.select = [pk.get_col(self.query.get_initial_alias())]
        outerq = Query(self.query.model)
        if not self.connection.features.update_can_self_select:
            # Force the materialization of the inner query to allow reference
            # to the target table on MySQL.
            sql, params = innerq.get_compiler(connection=self.connection).as_sql()
            innerq = RawSQL("SELECT * FROM (%s) subquery" % sql, params)
        outerq.add_filter("pk__in", innerq)
        return self._as_sql(outerq)