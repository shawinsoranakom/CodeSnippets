def test_onetoone_with_subclass(self):
        with self.assertNumQueries(1):
            p = Parent2.objects.select_related("child2").get(name2="Child2 Parent2")
            self.assertEqual(p.child2.name1, "Child2 Parent1")