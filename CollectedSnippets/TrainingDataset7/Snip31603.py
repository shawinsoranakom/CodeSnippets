def test_multiple_subclass(self):
        with self.assertNumQueries(1):
            p = Parent1.objects.select_related("child1").get(name1="Child1 Parent1")
            self.assertEqual(p.child1.name2, "Child1 Parent2")