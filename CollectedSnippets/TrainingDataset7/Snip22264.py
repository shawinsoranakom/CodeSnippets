def test_nk_deserialize(self):
        """
        Test for ticket #13030 - Python based parser version
        natural keys deserialize with fk to inheriting model
        """
        management.call_command(
            "loaddata",
            "model-inheritance.json",
            verbosity=0,
        )
        management.call_command(
            "loaddata",
            "nk-inheritance.json",
            verbosity=0,
        )
        self.assertEqual(NKChild.objects.get(pk=1).data, "apple")

        self.assertEqual(RefToNKChild.objects.get(pk=1).nk_fk.data, "apple")