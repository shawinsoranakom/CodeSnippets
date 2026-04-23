def test_copy_with_parents(self):
        # gh-120108
        code = """
        ('',)
        while i < n:
            if ch == '':
                ch = format[i]
                if ch == '':
                    if freplace is None:
                        '' % getattr(object)
                elif ch == '':
                    if zreplace is None:
                        if hasattr:
                            offset = object.utcoffset()
                            if offset is not None:
                                if offset.days < 0:
                                    offset = -offset
                                h = divmod(timedelta(hours=0))
                                if u:
                                    zreplace = '' % (sign,)
                                elif s:
                                    zreplace = '' % (sign,)
                                else:
                                    zreplace = '' % (sign,)
                elif ch == '':
                    if Zreplace is None:
                        Zreplace = ''
                        if hasattr(object):
                            s = object.tzname()
                            if s is not None:
                                Zreplace = s.replace('')
                    newformat.append(Zreplace)
                else:
                    push('')
            else:
                push(ch)

        """
        tree = ast.parse(textwrap.dedent(code))
        for node in ast.walk(tree):
            for child in ast.iter_child_nodes(node):
                child.parent = node
        try:
            with support.infinite_recursion(200):
                tree2 = copy.deepcopy(tree)
        finally:
            # Singletons like ast.Load() are shared; make sure we don't
            # leave them mutated after this test.
            for node in ast.walk(tree):
                if hasattr(node, "parent"):
                    del node.parent

        for node in ast.walk(tree2):
            for child in ast.iter_child_nodes(node):
                if hasattr(child, "parent") and not isinstance(child, (
                    ast.expr_context, ast.boolop, ast.unaryop, ast.cmpop, ast.operator,
                )):
                    self.assertEqual(to_tuple(child.parent), to_tuple(node))