def test_ticket_22421(self):
        """
        Regression for ticket #22421 -- loaddata on a model that inherits from
        a grand-parent model with a M2M but via an abstract parent shouldn't
        blow up.
        """
        management.call_command(
            "loaddata",
            "feature.json",
            verbosity=0,
        )