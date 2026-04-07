def test_parent_module_does_not_exist(self):
        msg = "Parent module urlpatterns_reverse.foo does not exist."
        with self.assertRaisesMessage(ViewDoesNotExist, msg):
            get_callable("urlpatterns_reverse.foo.bar")