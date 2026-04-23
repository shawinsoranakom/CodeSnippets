def doit(ty):
            p_type = getattr(P, ty)
            c_type = getattr(C, ty)
            for attr in dir(p_type):
                if attr.startswith('_'):
                    continue
                p_func = getattr(p_type, attr)
                c_func = getattr(c_type, attr)
                if inspect.isfunction(p_func):
                    p_sig = inspect.signature(p_func)
                    c_sig = inspect.signature(c_func)

                    # parameter names:
                    p_names = list(p_sig.parameters.keys())
                    c_names = [tr(x) for x in c_sig.parameters.keys()]

                    self.assertEqual(c_names, p_names,
                                     msg="parameter name mismatch in %s" % p_func)

                    p_kind = [x.kind for x in p_sig.parameters.values()]
                    c_kind = [x.kind for x in c_sig.parameters.values()]

                    # 'self' parameter:
                    self.assertIs(p_kind[0], POS_KWD)
                    self.assertIs(c_kind[0], POS)

                    # remaining parameters:
                    if ty == 'Decimal':
                        self.assertEqual(c_kind[1:], p_kind[1:],
                                         msg="parameter kind mismatch in %s" % p_func)
                    else: # Context methods are positional only in the C version.
                        self.assertEqual(len(c_kind), len(p_kind),
                                         msg="parameter kind mismatch in %s" % p_func)

                    # Run the function:
                    args, kwds = mkargs(C, c_sig)
                    try:
                        getattr(c_type(9), attr)(*args, **kwds)
                    except Exception:
                        raise TestFailed("invalid signature for %s: %s %s" % (c_func, args, kwds))

                    args, kwds = mkargs(P, p_sig)
                    try:
                        getattr(p_type(9), attr)(*args, **kwds)
                    except Exception:
                        raise TestFailed("invalid signature for %s: %s %s" % (p_func, args, kwds))