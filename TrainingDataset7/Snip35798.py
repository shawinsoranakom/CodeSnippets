def test_namespaced_view_detail(self):
        resolver = get_resolver("urlpatterns_reverse.nested_urls")
        self.assertTrue(resolver._is_callback("urlpatterns_reverse.nested_urls.view1"))
        self.assertTrue(resolver._is_callback("urlpatterns_reverse.nested_urls.view2"))
        self.assertTrue(resolver._is_callback("urlpatterns_reverse.nested_urls.View3"))
        self.assertFalse(resolver._is_callback("urlpatterns_reverse.nested_urls.blub"))