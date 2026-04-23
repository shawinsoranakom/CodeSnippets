def test_pg_sequence_resetting_checks(self):
        """
        Test for ticket #7565 -- PostgreSQL sequence resetting checks shouldn't
        ascend to parent models when inheritance is used
        (since they are treated individually).
        """
        management.call_command(
            "loaddata",
            "model-inheritance.json",
            verbosity=0,
        )
        self.assertEqual(Parent.objects.all()[0].id, 1)
        self.assertEqual(Child.objects.all()[0].id, 1)