def test15_invalid_select_related(self):
        """
        select_related on the related name manager of a unique FK.
        """
        qs = Article.objects.select_related("author__article")
        # This triggers TypeError when `get_default_columns` has no
        # `local_only` keyword. The TypeError is swallowed if QuerySet is
        # actually evaluated as list generation swallows TypeError in CPython.
        str(qs.query)