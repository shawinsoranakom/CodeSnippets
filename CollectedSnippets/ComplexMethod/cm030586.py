def test_inspect_module(self):
        for attr in dir(P):
            if attr.startswith('_'):
                continue
            p_func = getattr(P, attr)
            c_func = getattr(C, attr)
            if (attr == 'Decimal' or attr == 'Context' or
                inspect.isfunction(p_func)):
                p_sig = inspect.signature(p_func)
                c_sig = inspect.signature(c_func)

                # parameter names:
                c_names = list(c_sig.parameters.keys())
                p_names = [x for x in p_sig.parameters.keys() if not
                           x.startswith('_')]

                self.assertEqual(c_names, p_names,
                                 msg="parameter name mismatch in %s" % p_func)

                c_kind = [x.kind for x in c_sig.parameters.values()]
                p_kind = [x[1].kind for x in p_sig.parameters.items() if not
                          x[0].startswith('_')]

                # parameters:
                if attr != 'setcontext':
                    self.assertEqual(c_kind, p_kind,
                                     msg="parameter kind mismatch in %s" % p_func)