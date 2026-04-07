def test_overriding_FIELD_display(self):
        class FooBar(models.Model):
            foo_bar = models.IntegerField(choices=[(1, "foo"), (2, "bar")])

            def get_foo_bar_display(self):
                return "something"

        f = FooBar(foo_bar=1)
        self.assertEqual(f.get_foo_bar_display(), "something")