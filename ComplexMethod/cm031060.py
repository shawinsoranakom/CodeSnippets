def istest(self, predicate, exp):
        obj = eval(exp)
        self.assertTrue(predicate(obj), '%s(%s)' % (predicate.__name__, exp))

        for other in self.predicates - set([predicate]):
            if (predicate == inspect.isgeneratorfunction or \
               predicate == inspect.isasyncgenfunction or \
               predicate == inspect.iscoroutinefunction) and \
               other == inspect.isfunction:
                continue
            if predicate == inspect.ispackage and other == inspect.ismodule:
                self.assertTrue(predicate(obj), '%s(%s)' % (predicate.__name__, exp))
            else:
                self.assertFalse(other(obj), 'not %s(%s)' % (other.__name__, exp))