def test_replace_native(self):
        for klass in self.iter_ast_classes():
            fields = set(klass._fields)
            attributes = set(klass._attributes)

            with self.subTest(klass=klass, fields=fields, attributes=attributes):
                # use of object() to ensure that '==' and 'is'
                # behave similarly in ast.compare(node, repl)
                old_fields = {field: object() for field in fields}
                old_attrs = {attr: object() for attr in attributes}

                # check shallow copy
                node = klass(**old_fields)
                repl = copy.replace(node)
                self.assertTrue(ast.compare(node, repl, compare_attributes=True))
                # check when passing using attributes (they may be optional!)
                node = klass(**old_fields, **old_attrs)
                repl = copy.replace(node)
                self.assertTrue(ast.compare(node, repl, compare_attributes=True))

                for field in fields:
                    # check when we sometimes have attributes and sometimes not
                    for init_attrs in [{}, old_attrs]:
                        node = klass(**old_fields, **init_attrs)
                        # only change a single field (do not change attributes)
                        new_value = object()
                        repl = copy.replace(node, **{field: new_value})
                        for f in fields:
                            old_value = old_fields[f]
                            # assert that there is no side-effect
                            self.assertIs(getattr(node, f), old_value)
                            # check the changes
                            if f != field:
                                self.assertIs(getattr(repl, f), old_value)
                            else:
                                self.assertIs(getattr(repl, f), new_value)
                        self.assertFalse(ast.compare(node, repl, compare_attributes=True))

                for attribute in attributes:
                    node = klass(**old_fields, **old_attrs)
                    # only change a single attribute (do not change fields)
                    new_attr = object()
                    repl = copy.replace(node, **{attribute: new_attr})
                    for a in attributes:
                        old_attr = old_attrs[a]
                        # assert that there is no side-effect
                        self.assertIs(getattr(node, a), old_attr)
                        # check the changes
                        if a != attribute:
                            self.assertIs(getattr(repl, a), old_attr)
                        else:
                            self.assertIs(getattr(repl, a), new_attr)
                    self.assertFalse(ast.compare(node, repl, compare_attributes=True))