def test_view_does_not_exist(self):
        msg = "View does not exist in module urlpatterns_reverse.views."
        with self.assertRaisesMessage(ViewDoesNotExist, msg):
            get_callable("urlpatterns_reverse.views.i_should_not_exist")