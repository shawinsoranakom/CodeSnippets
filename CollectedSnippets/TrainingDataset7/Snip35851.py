def test_repr_extra_kwargs(self):
        self.assertEqual(
            repr(resolve("/mixed_args/1986/11/")),
            "ResolverMatch(func=urlpatterns_reverse.views.empty_view, args=(), "
            "kwargs={'arg2': '11', 'extra': True}, url_name='mixed-args', "
            "app_names=[], namespaces=[], "
            "route='^mixed_args/([0-9]+)/(?P<arg2>[0-9]+)/$', "
            "captured_kwargs={'arg2': '11'}, extra_kwargs={'extra': True})",
        )