def assertFieldType(name, definition):
            out_def = re.search(r"^\s*%s = (models.*)$" % name, output, re.MULTILINE)[1]
            self.assertEqual(definition, out_def)