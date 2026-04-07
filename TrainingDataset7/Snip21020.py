def test_saving_object_with_deferred_field(self):
        # Saving models with deferred fields is possible (but inefficient,
        # since every field has to be retrieved first).
        obj = Primary.objects.defer("value").get(name="p2")
        obj.name = "a new name"
        obj.save()
        self.assertQuerySetEqual(
            Primary.objects.all(),
            [
                "p1",
                "a new name",
            ],
            lambda p: p.name,
            ordered=False,
        )