def test_update_ordered_by_m2m_annotation(self):
        foo = Foo.objects.create(target="test")
        Bar.objects.create(foo=foo)

        Bar.objects.annotate(abs_id=Abs("m2m_foo")).order_by("abs_id").update(x=3)
        self.assertEqual(Bar.objects.get().x, 3)