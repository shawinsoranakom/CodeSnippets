def test_order_by_annotation_transform(self):
        class Mod2(Mod, Transform):
            def __init__(self, expr):
                super().__init__(expr, 2)

        output_field = IntegerField()
        output_field.register_lookup(Mod2, "mod2")
        qs1 = Number.objects.annotate(
            annotation=Value(1, output_field=output_field),
        )
        qs2 = Number.objects.annotate(
            annotation=Value(2, output_field=output_field),
        )
        msg = "Ordering combined queries by transforms is not implemented."
        with self.assertRaisesMessage(NotImplementedError, msg):
            list(qs1.union(qs2).order_by("annotation__mod2"))