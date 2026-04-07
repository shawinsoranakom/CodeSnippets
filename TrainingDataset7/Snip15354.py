def test_method_excludes(self):
        """
        Methods that begin with strings defined in
        ``django.contrib.admindocs.views.MODEL_METHODS_EXCLUDE``
        shouldn't be displayed in the admin docs.
        """
        self.assertContains(self.response, "<td>get_full_name</td>")
        self.assertNotContains(self.response, "<td>_get_full_name</td>")
        self.assertNotContains(self.response, "<td>add_image</td>")
        self.assertNotContains(self.response, "<td>delete_image</td>")
        self.assertNotContains(self.response, "<td>set_status</td>")
        self.assertNotContains(self.response, "<td>save_changes</td>")