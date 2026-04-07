def test_for_update_of_self_when_self_is_not_selected(self):
        """
        select_for_update(of=['self']) when the only columns selected are from
        related tables.
        """
        with transaction.atomic():
            values = list(
                Person.objects.select_related("born")
                .select_for_update(of=("self",))
                .values("born__name")
            )
        self.assertEqual(values, [{"born__name": self.city1.name}])