def test_boolean_conversion(self):
        """
        Testing Boolean value conversion with the spatial backend, see #15169.
        """
        t1 = Truth.objects.create(val=True)
        t2 = Truth.objects.create(val=False)

        val1 = Truth.objects.get(pk=t1.pk).val
        val2 = Truth.objects.get(pk=t2.pk).val
        # verify types -- shouldn't be 0/1
        self.assertIsInstance(val1, bool)
        self.assertIsInstance(val2, bool)
        # verify values
        self.assertIs(val1, True)
        self.assertIs(val2, False)