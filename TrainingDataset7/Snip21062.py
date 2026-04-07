def test_common_model_different_mask(self):
        child = Child.objects.create(name="Child", value=42)
        second_child = Child.objects.create(name="Second", value=64)
        Leaf.objects.create(child=child, second_child=second_child)
        with self.assertNumQueries(1):
            leaf = (
                Leaf.objects.select_related("child", "second_child")
                .defer("child__name", "second_child__value")
                .get()
            )
            self.assertEqual(leaf.child, child)
            self.assertEqual(leaf.second_child, second_child)
        self.assertEqual(leaf.child.get_deferred_fields(), {"name"})
        self.assertEqual(leaf.second_child.get_deferred_fields(), {"value"})
        with self.assertNumQueries(0):
            self.assertEqual(leaf.child.value, 42)
            self.assertEqual(leaf.second_child.name, "Second")
        with self.assertNumQueries(1):
            self.assertEqual(leaf.child.name, "Child")
        with self.assertNumQueries(1):
            self.assertEqual(leaf.second_child.value, 64)