def test_view_detail_as_method(self):
        # Views which have a class name as part of their path.
        resolver = get_resolver("urlpatterns_reverse.method_view_urls")
        self.assertTrue(
            resolver._is_callback(
                "urlpatterns_reverse.method_view_urls.ViewContainer.method_view"
            )
        )
        self.assertTrue(
            resolver._is_callback(
                "urlpatterns_reverse.method_view_urls.ViewContainer.classmethod_view"
            )
        )