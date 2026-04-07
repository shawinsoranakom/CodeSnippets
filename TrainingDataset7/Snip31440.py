def test_func_index_invalid_topmost_expressions(self):
        index = Index(Upper(F("name").desc()), name="name")
        msg = (
            "%s must be topmost expressions in an indexed expression."
            % self._index_expressions_wrappers()
        )
        with connection.schema_editor() as editor:
            with self.assertRaisesMessage(ValueError, msg):
                editor.add_index(Author, index)