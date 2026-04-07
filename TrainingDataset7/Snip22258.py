def test_loaddata_with_m2m_to_self(self):
        """
        Regression test for ticket #17946.
        """
        management.call_command(
            "loaddata",
            "m2mtoself.json",
            verbosity=0,
        )