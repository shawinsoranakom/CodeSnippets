def test_assigning_invalid_data_to_m2m_doesnt_clear_existing_relations(self):
        t1 = Tag.objects.create(name="t1")
        t2 = Tag.objects.create(name="t2")
        c1 = TagCollection.objects.create(name="c1")
        c1.tags.set([t1, t2])

        with self.assertRaisesMessage(TypeError, "'int' object is not iterable"):
            c1.tags.set(7)

        c1.refresh_from_db()
        self.assertSequenceEqual(c1.tags.order_by("name"), [t1, t2])