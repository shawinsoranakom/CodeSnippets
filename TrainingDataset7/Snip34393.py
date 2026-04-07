def test_file_does_not_exist(self):
        with self.assertRaises(TemplateDoesNotExist):
            self.engine.get_template("doesnotexist.html")