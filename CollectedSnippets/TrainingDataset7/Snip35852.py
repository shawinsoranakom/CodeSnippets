def test_classbased_repr(self):
        self.assertEqual(
            repr(resolve("/redirect/")),
            "ResolverMatch(func=urlpatterns_reverse.views.LazyRedirectView, "
            "args=(), kwargs={}, url_name=None, app_names=[], "
            "namespaces=[], route='redirect/')",
        )