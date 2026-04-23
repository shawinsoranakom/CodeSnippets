def test_inheritance(self):
        # Make sure the inheritance hierarchy matches the documentation
        exc_set = set()
        for object_ in builtins.__dict__.values():
            try:
                if issubclass(object_, BaseException):
                    exc_set.add(object_.__name__)
            except TypeError:
                pass

        inheritance_tree = open(
                os.path.join(os.path.split(__file__)[0], 'exception_hierarchy.txt'),
                encoding="utf-8")
        try:
            superclass_name = inheritance_tree.readline().rstrip()
            try:
                last_exc = getattr(builtins, superclass_name)
            except AttributeError:
                self.fail("base class %s not a built-in" % superclass_name)
            self.assertIn(superclass_name, exc_set,
                          '%s not found' % superclass_name)
            exc_set.discard(superclass_name)
            superclasses = []  # Loop will insert base exception
            last_depth = 0
            for exc_line in inheritance_tree:
                exc_line = exc_line.rstrip()
                depth = exc_line.rindex('─')
                exc_name = exc_line[depth+2:]  # Slice past space
                if '(' in exc_name:
                    paren_index = exc_name.index('(')
                    platform_name = exc_name[paren_index+1:-1]
                    exc_name = exc_name[:paren_index-1]  # Slice off space
                    if platform_system() != platform_name:
                        exc_set.discard(exc_name)
                        continue
                if '[' in exc_name:
                    left_bracket = exc_name.index('[')
                    exc_name = exc_name[:left_bracket-1]  # cover space
                try:
                    exc = getattr(builtins, exc_name)
                except AttributeError:
                    self.fail("%s not a built-in exception" % exc_name)
                if last_depth < depth:
                    superclasses.append((last_depth, last_exc))
                elif last_depth > depth:
                    while superclasses[-1][0] >= depth:
                        superclasses.pop()
                self.assertTrue(issubclass(exc, superclasses[-1][1]),
                "%s is not a subclass of %s" % (exc.__name__,
                    superclasses[-1][1].__name__))
                try:  # Some exceptions require arguments; just skip them
                    self.verify_instance_interface(exc())
                except TypeError:
                    pass
                self.assertIn(exc_name, exc_set)
                exc_set.discard(exc_name)
                last_exc = exc
                last_depth = depth
        finally:
            inheritance_tree.close()
        self.assertEqual(len(exc_set), 0, "%s not accounted for" % exc_set)