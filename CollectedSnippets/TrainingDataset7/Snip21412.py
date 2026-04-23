def test_expressions_not_introduce_sql_injection_via_untrusted_string_inclusion(
        self,
    ):
        """
        This tests that SQL injection isn't possible using compilation of
        expressions in iterable filters, as their compilation happens before
        the main query compilation. It's limited to SQLite, as PostgreSQL,
        Oracle and other vendors have defense in depth against this by type
        checking. Testing against SQLite (the most permissive of the built-in
        databases) demonstrates that the problem doesn't exist while keeping
        the test simple.
        """
        queryset = Company.objects.filter(name__in=[F("num_chairs") + "1)) OR ((1==1"])
        self.assertQuerySetEqual(queryset, [], ordered=False)