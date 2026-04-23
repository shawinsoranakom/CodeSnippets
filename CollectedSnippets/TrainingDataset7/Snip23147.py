def test_installed_apps_template_found(self):
        """Can find a custom template in INSTALLED_APPS."""
        renderer = self.renderer()
        # Found because forms_tests is .
        tpl = renderer.get_template("forms_tests/custom_widget.html")
        expected_path = os.path.abspath(
            os.path.join(
                os.path.dirname(__file__),
                "..",
                self.expected_widget_dir + "/forms_tests/custom_widget.html",
            )
        )
        self.assertEqual(tpl.origin.name, expected_path)