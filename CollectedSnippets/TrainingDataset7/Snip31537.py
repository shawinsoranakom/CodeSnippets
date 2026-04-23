def test_for_update_of_with_exists(self):
        with transaction.atomic():
            qs = Person.objects.select_for_update(of=("self", "born"))
            self.assertIs(qs.exists(), True)