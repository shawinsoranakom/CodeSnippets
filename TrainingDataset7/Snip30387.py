def test_custom_pk(self):
        custom_pks = [
            CustomPk.objects.create(name="pk-%s" % i, extra="") for i in range(10)
        ]
        for model in custom_pks:
            model.extra = "extra-%s" % model.pk
        CustomPk.objects.bulk_update(custom_pks, ["extra"])
        self.assertCountEqual(
            CustomPk.objects.values_list("extra", flat=True),
            [cat.extra for cat in custom_pks],
        )