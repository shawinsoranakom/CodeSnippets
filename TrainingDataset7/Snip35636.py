def test_update_respects_to_field(self):
        """
        Update of an FK field which specifies a to_field works.
        """
        a_foo = Foo.objects.create(target="aaa")
        b_foo = Foo.objects.create(target="bbb")
        bar = Bar.objects.create(foo=a_foo)
        self.assertEqual(bar.foo_id, a_foo.target)
        bar_qs = Bar.objects.filter(pk=bar.pk)
        self.assertEqual(bar_qs[0].foo_id, a_foo.target)
        bar_qs.update(foo=b_foo)
        self.assertEqual(bar_qs[0].foo_id, b_foo.target)