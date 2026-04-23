def test_for_update_of_followed_by_values_list(self):
        with transaction.atomic():
            values = list(
                Person.objects.select_for_update(of=("self",)).values_list("pk")
            )
        self.assertEqual(values, [(self.person.pk,)])