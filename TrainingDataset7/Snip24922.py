def test_language_prefix_with_script_prefix(self):
        prefix = "/script_prefix"
        with override_script_prefix(prefix):
            response = self.client.get(
                "/prefixed/", headers={"accept-language": "en"}, SCRIPT_NAME=prefix
            )
            self.assertRedirects(
                response, "%s/en/prefixed/" % prefix, target_status_code=404
            )