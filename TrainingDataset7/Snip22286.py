def test_dump_and_load_m2m_simple(self):
        """
        Test serializing and deserializing back models with simple M2M
        relations
        """
        a = M2MSimpleA.objects.create(data="a")
        b1 = M2MSimpleB.objects.create(data="b1")
        b2 = M2MSimpleB.objects.create(data="b2")
        a.b_set.add(b1)
        a.b_set.add(b2)

        out = StringIO()
        management.call_command(
            "dumpdata",
            "fixtures_regress.M2MSimpleA",
            "fixtures_regress.M2MSimpleB",
            use_natural_foreign_keys=True,
            stdout=out,
        )

        for model in [M2MSimpleA, M2MSimpleB]:
            model.objects.all().delete()

        objects = serializers.deserialize("json", out.getvalue())
        for obj in objects:
            obj.save()

        new_a = M2MSimpleA.objects.get_by_natural_key("a")
        self.assertCountEqual(new_a.b_set.all(), [b1, b2])