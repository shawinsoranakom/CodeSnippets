def test_multiinheritance_two_subclasses(self):
        with self.assertNumQueries(1):
            p = Parent1.objects.select_related("child1", "child1__child4").get(
                name1="Child1 Parent1"
            )
            self.assertEqual(p.child1.name2, "Child1 Parent2")
            self.assertEqual(p.child1.name1, p.name1)
            with self.assertRaises(Child4.DoesNotExist):
                p.child1.child4
        Child4(name1="n1", name2="n2", value=1, value4=4).save()
        with self.assertNumQueries(1):
            p = Parent2.objects.select_related("child1", "child1__child4").get(
                name2="n2"
            )
            self.assertEqual(p.name2, "n2")
            self.assertEqual(p.child1.name1, "n1")
            self.assertEqual(p.child1.name2, p.name2)
            self.assertEqual(p.child1.value, 1)
            self.assertEqual(p.child1.child4.name1, p.child1.name1)
            self.assertEqual(p.child1.child4.name2, p.child1.name2)
            self.assertEqual(p.child1.child4.value, p.child1.value)
            self.assertEqual(p.child1.child4.value4, 4)