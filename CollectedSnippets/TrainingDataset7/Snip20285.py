def test_save(self):
        """
        custom pks do not affect save
        """
        fran = Employee.objects.get(pk=456)
        fran.last_name = "Jones"
        fran.save()

        self.assertSequenceEqual(
            Employee.objects.filter(last_name="Jones"),
            [self.dan, fran],
        )