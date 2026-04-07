def test_custom_name_with_app_within_other_app(self):
        parent_app_dir = os.path.join(self.test_dir, "parent")
        self.run_django_admin(["startapp", "parent"])
        self.assertTrue(os.path.exists(parent_app_dir))

        nested_args = ["startapp", "child", "parent/child"]
        child_app_dir = os.path.join(self.test_dir, "parent", "child")
        out, err = self.run_django_admin(nested_args)
        self.assertNoOutput(out)
        self.assertNoOutput(err)
        self.assertTrue(os.path.exists(child_app_dir))