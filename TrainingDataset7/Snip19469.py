def test_contains_tuple_not_url_instance(self):
        result = check_url_config(None)
        warning = result[0]
        self.assertEqual(warning.id, "urls.E004")
        self.assertRegex(
            warning.msg,
            (
                r"^Your URL pattern \('\^tuple/\$', <function <lambda> at 0x(\w+)>\) "
                r"is invalid. Ensure that urlpatterns is a list of path\(\) and/or "
                r"re_path\(\) instances\.$"
            ),
        )