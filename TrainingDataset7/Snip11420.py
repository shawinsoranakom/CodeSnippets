def get_extra_restriction(self, alias, related_alias):
        """
        Return a pair condition used for joining and subquery pushdown. The
        condition is something that responds to as_sql(compiler, connection)
        method.

        Note that currently referring both the 'alias' and 'related_alias'
        will not work in some conditions, like subquery pushdown.

        A parallel method is get_extra_descriptor_filter() which is used in
        instance.fieldname related object fetching.
        """
        return None