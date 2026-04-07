def as_sql(self):
        """
        Create the SQL for this query. Return the SQL string and list of
        parameters.
        """
        sql, params = [], []
        for annotation in self.query.annotation_select.values():
            ann_sql, ann_params = self.compile(annotation)
            ann_sql, ann_params = annotation.select_format(self, ann_sql, ann_params)
            sql.append(ann_sql)
            params.extend(ann_params)
        self.col_count = len(self.query.annotation_select)
        sql = ", ".join(sql)
        params = tuple(params)

        inner_query_sql, inner_query_params = self.query.inner_query.get_compiler(
            self.using,
            elide_empty=self.elide_empty,
        ).as_sql(with_col_aliases=True)
        sql = "SELECT %s FROM (%s) subquery" % (sql, inner_query_sql)
        params += inner_query_params
        return sql, params