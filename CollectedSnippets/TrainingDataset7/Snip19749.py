def test_single_condition_head(self):
        self.client.defaults["HTTP_IF_MODIFIED_SINCE"] = LAST_MODIFIED_STR
        response = self.client.head("/condition/")
        self.assertNotModified(response)