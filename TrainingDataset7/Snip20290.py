def test_custom_field_pk(self):
        # Regression for #10785 -- Custom fields can be used for primary keys.
        new_bar = Bar.objects.create()
        new_foo = Foo.objects.create(bar=new_bar)

        f = Foo.objects.get(bar=new_bar.pk)
        self.assertEqual(f, new_foo)
        self.assertEqual(f.bar, new_bar)

        f = Foo.objects.get(bar=new_bar)
        self.assertEqual(f, new_foo)
        self.assertEqual(f.bar, new_bar)