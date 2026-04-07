def test_inheritance_deferred(self):
        c = Child4.objects.create(name1="n1", name2="n2", value=1, value4=4)
        with self.assertNumQueries(1):
            p = (
                Parent2.objects.select_related("child1")
                .only("id2", "child1__value")
                .get(name2="n2")
            )
            self.assertEqual(p.id2, c.id2)
            self.assertEqual(p.child1.value, 1)
        p = (
            Parent2.objects.select_related("child1")
            .only("id2", "child1__value")
            .get(name2="n2")
        )
        with self.assertNumQueries(1):
            self.assertEqual(p.name2, "n2")
        p = (
            Parent2.objects.select_related("child1")
            .only("id2", "child1__value")
            .get(name2="n2")
        )
        with self.assertNumQueries(1):
            self.assertEqual(p.child1.name2, "n2")