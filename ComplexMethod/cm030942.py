def do_test_remove_with_clear(self, *, raises):

        # Until the discrepency between "del root[:]" and "root.clear()" is
        # resolved, we need to keep two tests. Previously, using "del root[:]"
        # did not crash with the reproducer of gh-126033 while "root.clear()"
        # did.

        class E(ET.Element):
            """Local class to be able to mock E.__eq__ for introspection."""

        class X(E):
            def __eq__(self, o):
                del root[:]
                return not raises

        class Y(E):
            def __eq__(self, o):
                root.clear()
                return not raises

        if raises:
            get_checker_context = lambda: self.assertRaises(ValueError)
        else:
            get_checker_context = nullcontext

        self.assertIs(E.__eq__, object.__eq__)

        for Z, side_effect in [(X, 'del root[:]'), (Y, 'root.clear()')]:
            self.enterContext(self.subTest(side_effect=side_effect))

            # test removing R() from [U()]
            for R, U, description in [
                (E, Z, "remove missing E() from [Z()]"),
                (Z, E, "remove missing Z() from [E()]"),
                (Z, Z, "remove missing Z() from [Z()]"),
            ]:
                with self.subTest(description):
                    root = E('top')
                    root.extend([U('one')])
                    with get_checker_context():
                        root.remove(R('missing'))

            # test removing R() from [U(), V()]
            cases = self.cases_for_remove_missing_with_mutations(E, Z)
            for R, U, V, description in cases:
                with self.subTest(description):
                    root = E('top')
                    root.extend([U('one'), V('two')])
                    with get_checker_context():
                        root.remove(R('missing'))

            # Test removing root[0] from [Z()].
            #
            # Since we call root.remove() with root[0], Z.__eq__()
            # will not be called (we branch on the fast Py_EQ path).
            with self.subTest("remove root[0] from [Z()]"):
                root = E('top')
                root.append(Z('rem'))
                with equal_wrapper(E) as f, equal_wrapper(Z) as g:
                    root.remove(root[0])
                f.assert_not_called()
                g.assert_not_called()

            # Test removing root[1] (of type R) from [U(), R()].
            is_special = is_python_implementation() and raises and Z is Y
            if is_python_implementation() and raises and Z is Y:
                # In pure Python, using root.clear() sets the children
                # list to [] without calling list.clear().
                #
                # For this reason, the call to root.remove() first
                # checks root[0] and sets the children list to []
                # since either root[0] or root[1] is an evil element.
                #
                # Since checking root[1] still uses the old reference
                # to the children list, PyObject_RichCompareBool() branches
                # to the fast Py_EQ path and Y.__eq__() is called exactly
                # once (when checking root[0]).
                continue
            else:
                cases = self.cases_for_remove_existing_with_mutations(E, Z)
                for R, U, description in cases:
                    with self.subTest(description):
                        root = E('top')
                        root.extend([U('one'), R('rem')])
                        with get_checker_context():
                            root.remove(root[1])