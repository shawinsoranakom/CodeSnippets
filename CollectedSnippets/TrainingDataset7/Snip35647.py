def test_update_ordered_by_inline_m2m_annotation(self):
        foo = Foo.objects.create(target="test")
        Bar.objects.create(foo=foo)

        Bar.objects.order_by(Abs("m2m_foo")).update(x=2)
        self.assertEqual(Bar.objects.get().x, 2)