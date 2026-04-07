def test_parent_only(self):
        with self.assertNumQueries(1):
            p = Parent1.objects.select_related("child1").get(name1="Only Parent1")
        with self.assertNumQueries(0):
            with self.assertRaises(Child1.DoesNotExist):
                p.child1