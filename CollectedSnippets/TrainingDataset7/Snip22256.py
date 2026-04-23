def test_ticket_20820(self):
        """
        Regression for ticket #20820 -- loaddata on a model that inherits
        from a model with a M2M shouldn't blow up.
        """
        management.call_command(
            "loaddata",
            "special-article.json",
            verbosity=0,
        )