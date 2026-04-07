def test_duplicate_order_field(self):
        class Bar(models.Model):
            class Meta:
                app_label = "order_with_respect_to"

        class Foo(models.Model):
            bar = models.ForeignKey(Bar, models.CASCADE)
            order = models.OrderWrt()

            class Meta:
                order_with_respect_to = "bar"
                app_label = "order_with_respect_to"

        count = 0
        for field in Foo._meta.local_fields:
            if isinstance(field, models.OrderWrt):
                count += 1

        self.assertEqual(count, 1)