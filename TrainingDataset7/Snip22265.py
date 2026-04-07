def test_nk_deserialize_xml(self):
        """
        Test for ticket #13030 - XML version
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
        management.call_command(
            "loaddata",
            "nk-inheritance2.xml",
            verbosity=0,
        )
        self.assertEqual(NKChild.objects.get(pk=2).data, "banana")
        self.assertEqual(RefToNKChild.objects.get(pk=2).nk_fk.data, "apple")