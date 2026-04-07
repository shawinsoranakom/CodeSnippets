def test_attributeerror_not_hidden(self):
        msg = "I am here to confuse django.urls.get_callable"
        with self.assertRaisesMessage(AttributeError, msg):
            get_callable("urlpatterns_reverse.views_broken.i_am_broken")