def test_reverse_by_path_nested(self):
        # Views added to urlpatterns using include() should be reversible.
        from .views import nested_view

        self.assertEqual(reverse(nested_view), "/includes/nested_path/")