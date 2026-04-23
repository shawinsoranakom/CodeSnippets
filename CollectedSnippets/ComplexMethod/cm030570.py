def _check_in_scopes(self, code, outputs=None, ns=None, scopes=None, raises=(),
                         exec_func=exec):
        code = textwrap.dedent(code)
        scopes = scopes or ["module", "class", "function"]
        for scope in scopes:
            with self.subTest(scope=scope):
                if scope == "class":
                    newcode = textwrap.dedent("""
                        class _C:
                            {code}
                    """).format(code=textwrap.indent(code, "    "))
                    def get_output(moddict, name):
                        return getattr(moddict["_C"], name)
                elif scope == "function":
                    newcode = textwrap.dedent("""
                        def _f():
                            {code}
                            return locals()
                        _out = _f()
                    """).format(code=textwrap.indent(code, "    "))
                    def get_output(moddict, name):
                        return moddict["_out"][name]
                else:
                    newcode = code
                    def get_output(moddict, name):
                        return moddict[name]
                newns = ns.copy() if ns else {}
                try:
                    exec_func(newcode, newns)
                except raises as e:
                    # We care about e.g. NameError vs UnboundLocalError
                    self.assertIs(type(e), raises)
                else:
                    for k, v in (outputs or {}).items():
                        self.assertEqual(get_output(newns, k), v, k)