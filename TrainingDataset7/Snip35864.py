def test_not_callable(self):
        msg = (
            "Could not import 'urlpatterns_reverse.tests.resolve_test_data'. "
            "View is not callable."
        )
        with self.assertRaisesMessage(ViewDoesNotExist, msg):
            get_callable("urlpatterns_reverse.tests.resolve_test_data")