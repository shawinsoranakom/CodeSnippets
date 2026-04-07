def test_script_name_escaping(self):
        self.assertEqual(
            reverse("optional", args=["foo:bar"]), "/script:name/optional/foo:bar/"
        )