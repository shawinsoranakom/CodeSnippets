def test_resolver_repr(self):
        """
        Test repr of URLResolver, especially when urlconf_name is a list
        (#17892).
        """
        # Pick a resolver from a namespaced URLconf
        resolver = get_resolver("urlpatterns_reverse.namespace_urls")
        sub_resolver = resolver.namespace_dict["test-ns1"][1]
        self.assertIn("<URLPattern list>", repr(sub_resolver))