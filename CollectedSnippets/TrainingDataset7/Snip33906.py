def test_undefined_partial_exception_info_template_does_not_exist(self):
        with self.assertRaises(TemplateDoesNotExist) as cm:
            self.engine.get_template("existing_template#undefined")

        self.assertIn("undefined", str(cm.exception))