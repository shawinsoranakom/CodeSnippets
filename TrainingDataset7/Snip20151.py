def test_transform_order_by(self):
        with register_lookup(models.IntegerField, LastDigitTransform):
            a1 = Author.objects.create(name="a1", age=11)
            a2 = Author.objects.create(name="a2", age=23)
            a3 = Author.objects.create(name="a3", age=32)
            a4 = Author.objects.create(name="a4", age=40)
            qs = Author.objects.order_by("age__lastdigit")
            self.assertSequenceEqual(qs, [a4, a1, a3, a2])