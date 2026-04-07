def test_save_parent_after_assign(self):
        category = Category(name="cats")
        record = Record(category=category)
        category.save()
        record.save()
        category.name = "dogs"
        with self.assertNumQueries(0):
            self.assertEqual(category.id, record.category_id)
            self.assertEqual(category.name, record.category.name)