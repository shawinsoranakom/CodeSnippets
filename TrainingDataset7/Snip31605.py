def test_onetoone_with_two_subclasses(self):
        with self.assertNumQueries(1):
            p = Parent2.objects.select_related("child2", "child2__child3").get(
                name2="Child2 Parent2"
            )
            self.assertEqual(p.child2.name1, "Child2 Parent1")
            with self.assertRaises(Child3.DoesNotExist):
                p.child2.child3
        p3 = Parent2(name2="Child3 Parent2")
        p3.save()
        c2 = Child3(name1="Child3 Parent1", parent2=p3, value=2, value3=3)
        c2.save()
        with self.assertNumQueries(1):
            p = Parent2.objects.select_related("child2", "child2__child3").get(
                name2="Child3 Parent2"
            )
            self.assertEqual(p.child2.name1, "Child3 Parent1")
            self.assertEqual(p.child2.child3.value3, 3)
            self.assertEqual(p.child2.child3.value, p.child2.value)
            self.assertEqual(p.child2.name1, p.child2.child3.name1)