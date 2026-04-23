def explain(self, *, format=None, **options):
        """
        Runs an EXPLAIN on the SQL query this QuerySet would perform, and
        returns the results.
        """
        return self.query.explain(using=self.db, format=format, **options)