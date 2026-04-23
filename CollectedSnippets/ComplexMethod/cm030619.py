def test_inspect_classify_class_attrs(self):
        # indirectly test __objclass__
        from inspect import Attribute
        values = [
                Attribute(name='__class__', kind='data',
                    defining_class=object, object=EnumType),
                Attribute(name='__contains__', kind='method',
                    defining_class=EnumType, object=self.Color.__contains__),
                Attribute(name='__doc__', kind='data',
                    defining_class=self.Color, object='...'),
                Attribute(name='__getitem__', kind='method',
                    defining_class=EnumType, object=self.Color.__getitem__),
                Attribute(name='__iter__', kind='method',
                    defining_class=EnumType, object=self.Color.__iter__),
                Attribute(name='__init_subclass__', kind='class method',
                    defining_class=object, object=getattr(self.Color, '__init_subclass__')),
                Attribute(name='__len__', kind='method',
                    defining_class=EnumType, object=self.Color.__len__),
                Attribute(name='__members__', kind='property',
                    defining_class=EnumType, object=EnumType.__members__),
                Attribute(name='__module__', kind='data',
                    defining_class=self.Color, object=__name__),
                Attribute(name='__name__', kind='data',
                    defining_class=self.Color, object='Color'),
                Attribute(name='__qualname__', kind='data',
                    defining_class=self.Color, object='TestStdLib.Color'),
                Attribute(name='YELLOW', kind='data',
                    defining_class=self.Color, object=self.Color.YELLOW),
                Attribute(name='MAGENTA', kind='data',
                    defining_class=self.Color, object=self.Color.MAGENTA),
                Attribute(name='CYAN', kind='data',
                    defining_class=self.Color, object=self.Color.CYAN),
                Attribute(name='name', kind='data',
                    defining_class=Enum, object=Enum.__dict__['name']),
                Attribute(name='value', kind='data',
                    defining_class=Enum, object=Enum.__dict__['value']),
                ]
        for v in values:
            try:
                v.name
            except AttributeError:
                print(v)
        values.sort(key=lambda item: item.name)
        result = list(inspect.classify_class_attrs(self.Color))
        result.sort(key=lambda item: item.name)
        self.assertEqual(
                len(values), len(result),
                "%s != %s" % ([a.name for a in values], [a.name for a in result])
                )
        failed = False
        for v, r in zip(values, result):
            if r.name in ('__init_subclass__', '__doc__'):
                # not sure how to make the __init_subclass_ Attributes match
                # so as long as there is one, call it good
                # __doc__ is too big to check exactly, so treat the same as __init_subclass__
                for name in ('name','kind','defining_class'):
                    if getattr(v, name) != getattr(r, name):
                        print('\n%s\n%s\n%s\n%s\n' % ('=' * 75, r, v, '=' * 75), sep='')
                        failed = True
            elif r != v:
                print('\n%s\n%s\n%s\n%s\n' % ('=' * 75, r, v, '=' * 75), sep='')
                failed = True
        if failed:
            self.fail("result does not equal expected, see print above")