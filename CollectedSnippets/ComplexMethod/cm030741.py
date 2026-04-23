def test_longargs(self):
        for tree in self.parse_all(longargs, minver=8):
            for t in tree.body:
                # The expected args are encoded in the function name
                todo = set(t.name[1:])
                self.assertEqual(len(t.args.args) + len(t.args.posonlyargs),
                                 len(todo) - bool(t.args.vararg) - bool(t.args.kwarg))
                self.assertStartsWith(t.name, 'f')
                for index, c in enumerate(t.name[1:]):
                    todo.remove(c)
                    if c == 'v':
                        arg = t.args.vararg
                    elif c == 'k':
                        arg = t.args.kwarg
                    else:
                        assert 0 <= ord(c) - ord('a') < len(t.args.posonlyargs + t.args.args)
                        if index < len(t.args.posonlyargs):
                            arg = t.args.posonlyargs[ord(c) - ord('a')]
                        else:
                            arg = t.args.args[ord(c) - ord('a') - len(t.args.posonlyargs)]
                    self.assertEqual(arg.arg, c)  # That's the argument name
                    self.assertEqual(arg.type_comment, arg.arg.upper())
                assert not todo
        tree = self.classic_parse(longargs)
        for t in tree.body:
            for arg in t.args.args + [t.args.vararg, t.args.kwarg]:
                if arg is not None:
                    self.assertIsNone(arg.type_comment, "%s(%s:%r)" %
                                      (t.name, arg.arg, arg.type_comment))