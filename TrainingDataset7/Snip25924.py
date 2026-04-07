def test_add_m2m_with_base_class(self):
        # Regression for #11956 -- You can add an object to a m2m with the
        # base class without causing integrity errors

        t1 = Tag.objects.create(name="t1")
        t2 = Tag.objects.create(name="t2")

        c1 = TagCollection.objects.create(name="c1")
        c1.tags.set([t1, t2])
        c1 = TagCollection.objects.get(name="c1")

        self.assertCountEqual(c1.tags.all(), [t1, t2])
        self.assertCountEqual(t1.tag_collections.all(), [c1])