def test_view_loading(self):
        self.assertEqual(
            get_callable("urlpatterns_reverse.views.empty_view"), empty_view
        )
        self.assertEqual(get_callable(empty_view), empty_view)