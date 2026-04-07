def test_order_by_resetting(self):
        # Calling order_by() with no parameters removes any existing ordering
        # on the model. But it should still be possible to add new ordering
        # after that.
        qs = Author.objects.order_by().order_by("name")
        self.assertIn("ORDER BY", qs.query.get_compiler(qs.db).as_sql()[0])