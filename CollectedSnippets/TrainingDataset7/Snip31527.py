def test_for_update_of_values_list(self):
        queries = Person.objects.select_for_update(
            of=("self",),
        ).values_list(Concat(Value("Dr. "), F("name")), "born")
        with transaction.atomic():
            values = queries.get(pk=self.person.pk)
        self.assertSequenceEqual(values, ("Dr. Reinhardt", self.city1.pk))