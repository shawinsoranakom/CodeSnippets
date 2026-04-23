def basic_test(self, cf):
        E = ['Commented Bar',
             'Foo Bar',
             'Internationalized Stuff',
             'Long Line',
             'Section\\with$weird%characters[\t',
             'Spaces',
             'Spacey Bar',
             'Spacey Bar From The Beginning',
             'Types',
             'This One Has A ] In It',
             ]

        if self.allow_no_value:
            E.append('NoValue')
        E.sort()
        F = [('baz', 'qwe'), ('foo', 'bar3')]

        # API access
        L = cf.sections()
        L.sort()
        eq = self.assertEqual
        eq(L, E)
        L = cf.items('Spacey Bar From The Beginning')
        L.sort()
        eq(L, F)

        # mapping access
        L = [section for section in cf]
        L.sort()
        E.append(self.default_section)
        E.sort()
        eq(L, E)
        L = cf['Spacey Bar From The Beginning'].items()
        L = sorted(list(L))
        eq(L, F)
        L = cf.items()
        L = sorted(list(L))
        self.assertEqual(len(L), len(E))
        for name, section in L:
            eq(name, section.name)
        eq(cf.defaults(), cf[self.default_section])

        # The use of spaces in the section names serves as a
        # regression test for SourceForge bug #583248:
        # https://bugs.python.org/issue583248

        # API access
        eq(cf.get('Foo Bar', 'foo'), 'bar1')
        eq(cf.get('Spacey Bar', 'foo'), 'bar2')
        eq(cf.get('Spacey Bar From The Beginning', 'foo'), 'bar3')
        eq(cf.get('Spacey Bar From The Beginning', 'baz'), 'qwe')
        eq(cf.get('Commented Bar', 'foo'), 'bar4')
        eq(cf.get('Commented Bar', 'baz'), 'qwe')
        eq(cf.get('Spaces', 'key with spaces'), 'value')
        eq(cf.get('Spaces', 'another with spaces'), 'splat!')
        eq(cf.getint('Types', 'int'), 42)
        eq(cf.get('Types', 'int'), "42")
        self.assertAlmostEqual(cf.getfloat('Types', 'float'), 0.44)
        eq(cf.get('Types', 'float'), "0.44")
        eq(cf.getboolean('Types', 'boolean'), False)
        eq(cf.get('Types', '123'), 'strange but acceptable')
        eq(cf.get('This One Has A ] In It', 'forks'), 'spoons')
        if self.allow_no_value:
            eq(cf.get('NoValue', 'option-without-value'), None)

        # test vars= and fallback=
        eq(cf.get('Foo Bar', 'foo', fallback='baz'), 'bar1')
        eq(cf.get('Foo Bar', 'foo', vars={'foo': 'baz'}), 'baz')
        with self.assertRaises(configparser.NoSectionError):
            cf.get('No Such Foo Bar', 'foo')
        with self.assertRaises(configparser.NoOptionError):
            cf.get('Foo Bar', 'no-such-foo')
        eq(cf.get('No Such Foo Bar', 'foo', fallback='baz'), 'baz')
        eq(cf.get('Foo Bar', 'no-such-foo', fallback='baz'), 'baz')
        eq(cf.get('Spacey Bar', 'foo', fallback=None), 'bar2')
        eq(cf.get('No Such Spacey Bar', 'foo', fallback=None), None)
        eq(cf.getint('Types', 'int', fallback=18), 42)
        eq(cf.getint('Types', 'no-such-int', fallback=18), 18)
        eq(cf.getint('Types', 'no-such-int', fallback="18"), "18") # sic!
        with self.assertRaises(configparser.NoOptionError):
            cf.getint('Types', 'no-such-int')
        self.assertAlmostEqual(cf.getfloat('Types', 'float',
                                           fallback=0.0), 0.44)
        self.assertAlmostEqual(cf.getfloat('Types', 'no-such-float',
                                           fallback=0.0), 0.0)
        eq(cf.getfloat('Types', 'no-such-float', fallback="0.0"), "0.0") # sic!
        with self.assertRaises(configparser.NoOptionError):
            cf.getfloat('Types', 'no-such-float')
        eq(cf.getboolean('Types', 'boolean', fallback=True), False)
        eq(cf.getboolean('Types', 'no-such-boolean', fallback="yes"),
           "yes") # sic!
        eq(cf.getboolean('Types', 'no-such-boolean', fallback=True), True)
        with self.assertRaises(configparser.NoOptionError):
            cf.getboolean('Types', 'no-such-boolean')
        eq(cf.getboolean('No Such Types', 'boolean', fallback=True), True)
        if self.allow_no_value:
            eq(cf.get('NoValue', 'option-without-value', fallback=False), None)
            eq(cf.get('NoValue', 'no-such-option-without-value',
                      fallback=False), False)

        # mapping access
        eq(cf['Foo Bar']['foo'], 'bar1')
        eq(cf['Spacey Bar']['foo'], 'bar2')
        section = cf['Spacey Bar From The Beginning']
        eq(section.name, 'Spacey Bar From The Beginning')
        self.assertIs(section.parser, cf)
        with self.assertRaises(AttributeError):
            section.name = 'Name is read-only'
        with self.assertRaises(AttributeError):
            section.parser = 'Parser is read-only'
        eq(section['foo'], 'bar3')
        eq(section['baz'], 'qwe')
        eq(cf['Commented Bar']['foo'], 'bar4')
        eq(cf['Commented Bar']['baz'], 'qwe')
        eq(cf['Spaces']['key with spaces'], 'value')
        eq(cf['Spaces']['another with spaces'], 'splat!')
        eq(cf['Long Line']['foo'],
           'this line is much, much longer than my editor\nlikes it.')
        if self.allow_no_value:
            eq(cf['NoValue']['option-without-value'], None)
        # test vars= and fallback=
        eq(cf['Foo Bar'].get('foo', 'baz'), 'bar1')
        eq(cf['Foo Bar'].get('foo', fallback='baz'), 'bar1')
        eq(cf['Foo Bar'].get('foo', vars={'foo': 'baz'}), 'baz')
        with self.assertRaises(KeyError):
            cf['No Such Foo Bar']['foo']
        with self.assertRaises(KeyError):
            cf['Foo Bar']['no-such-foo']
        with self.assertRaises(KeyError):
            cf['No Such Foo Bar'].get('foo', fallback='baz')
        eq(cf['Foo Bar'].get('no-such-foo', 'baz'), 'baz')
        eq(cf['Foo Bar'].get('no-such-foo', fallback='baz'), 'baz')
        eq(cf['Foo Bar'].get('no-such-foo'), None)
        eq(cf['Spacey Bar'].get('foo', None), 'bar2')
        eq(cf['Spacey Bar'].get('foo', fallback=None), 'bar2')
        with self.assertRaises(KeyError):
            cf['No Such Spacey Bar'].get('foo', None)
        eq(cf['Types'].getint('int', 18), 42)
        eq(cf['Types'].getint('int', fallback=18), 42)
        eq(cf['Types'].getint('no-such-int', 18), 18)
        eq(cf['Types'].getint('no-such-int', fallback=18), 18)
        eq(cf['Types'].getint('no-such-int', "18"), "18") # sic!
        eq(cf['Types'].getint('no-such-int', fallback="18"), "18") # sic!
        eq(cf['Types'].getint('no-such-int'), None)
        self.assertAlmostEqual(cf['Types'].getfloat('float', 0.0), 0.44)
        self.assertAlmostEqual(cf['Types'].getfloat('float',
                                                    fallback=0.0), 0.44)
        self.assertAlmostEqual(cf['Types'].getfloat('no-such-float', 0.0), 0.0)
        self.assertAlmostEqual(cf['Types'].getfloat('no-such-float',
                                                    fallback=0.0), 0.0)
        eq(cf['Types'].getfloat('no-such-float', "0.0"), "0.0") # sic!
        eq(cf['Types'].getfloat('no-such-float', fallback="0.0"), "0.0") # sic!
        eq(cf['Types'].getfloat('no-such-float'), None)
        eq(cf['Types'].getboolean('boolean', True), False)
        eq(cf['Types'].getboolean('boolean', fallback=True), False)
        eq(cf['Types'].getboolean('no-such-boolean', "yes"), "yes") # sic!
        eq(cf['Types'].getboolean('no-such-boolean', fallback="yes"),
           "yes") # sic!
        eq(cf['Types'].getboolean('no-such-boolean', True), True)
        eq(cf['Types'].getboolean('no-such-boolean', fallback=True), True)
        eq(cf['Types'].getboolean('no-such-boolean'), None)
        if self.allow_no_value:
            eq(cf['NoValue'].get('option-without-value', False), None)
            eq(cf['NoValue'].get('option-without-value', fallback=False), None)
            eq(cf['NoValue'].get('no-such-option-without-value', False), False)
            eq(cf['NoValue'].get('no-such-option-without-value',
                      fallback=False), False)

        # Make sure the right things happen for remove_section() and
        # remove_option(); added to include check for SourceForge bug #123324.

        cf[self.default_section]['this_value'] = '1'
        cf[self.default_section]['that_value'] = '2'

        # API access
        self.assertTrue(cf.remove_section('Spaces'))
        self.assertFalse(cf.has_option('Spaces', 'key with spaces'))
        self.assertFalse(cf.remove_section('Spaces'))
        self.assertFalse(cf.remove_section(self.default_section))
        self.assertTrue(cf.remove_option('Foo Bar', 'foo'),
                        "remove_option() failed to report existence of option")
        self.assertFalse(cf.has_option('Foo Bar', 'foo'),
                    "remove_option() failed to remove option")
        self.assertFalse(cf.remove_option('Foo Bar', 'foo'),
                    "remove_option() failed to report non-existence of option"
                    " that was removed")
        self.assertTrue(cf.has_option('Foo Bar', 'this_value'))
        self.assertFalse(cf.remove_option('Foo Bar', 'this_value'))
        self.assertTrue(cf.remove_option(self.default_section, 'this_value'))
        self.assertFalse(cf.has_option('Foo Bar', 'this_value'))
        self.assertFalse(cf.remove_option(self.default_section, 'this_value'))

        with self.assertRaises(configparser.NoSectionError) as cm:
            cf.remove_option('No Such Section', 'foo')
        self.assertEqual(cm.exception.args, ('No Such Section',))

        eq(cf.get('Long Line', 'foo'),
           'this line is much, much longer than my editor\nlikes it.')

        # mapping access
        del cf['Types']
        self.assertFalse('Types' in cf)
        with self.assertRaises(KeyError):
            del cf['Types']
        with self.assertRaises(ValueError):
            del cf[self.default_section]
        del cf['Spacey Bar']['foo']
        self.assertFalse('foo' in cf['Spacey Bar'])
        with self.assertRaises(KeyError):
            del cf['Spacey Bar']['foo']
        self.assertTrue('that_value' in cf['Spacey Bar'])
        with self.assertRaises(KeyError):
            del cf['Spacey Bar']['that_value']
        del cf[self.default_section]['that_value']
        self.assertFalse('that_value' in cf['Spacey Bar'])
        with self.assertRaises(KeyError):
            del cf[self.default_section]['that_value']
        with self.assertRaises(KeyError):
            del cf['No Such Section']['foo']