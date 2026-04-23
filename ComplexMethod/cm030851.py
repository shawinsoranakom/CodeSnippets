def test_recursive_glob(self):
        eq = self.assertSequencesEqual_noorder
        full = [('EF',), ('ZZZ',),
                ('a',), ('a', 'D'),
                ('a', 'bcd'),
                ('a', 'bcd', 'EF'),
                ('a', 'bcd', 'efg'),
                ('a', 'bcd', 'efg', 'ha'),
                ('aaa',), ('aaa', 'zzzF'),
                ('aab',), ('aab', 'F'),
               ]
        if can_symlink():
            full += [('sym1',), ('sym2',),
                     ('sym3',),
                     ('sym3', 'EF'),
                     ('sym3', 'efg'),
                     ('sym3', 'efg', 'ha'),
                    ]
        eq(self.rglob('**'), self.joins(('',), *full))
        eq(self.rglob(os.curdir, '**'),
            self.joins((os.curdir, ''), *((os.curdir,) + i for i in full)))
        dirs = [('a', ''), ('a', 'bcd', ''), ('a', 'bcd', 'efg', ''),
                ('aaa', ''), ('aab', '')]
        if can_symlink():
            dirs += [('sym3', ''), ('sym3', 'efg', '')]
        eq(self.rglob('**', ''), self.joins(('',), *dirs))

        eq(self.rglob('a', '**'), self.joins(
            ('a', ''), ('a', 'D'), ('a', 'bcd'), ('a', 'bcd', 'EF'),
            ('a', 'bcd', 'efg'), ('a', 'bcd', 'efg', 'ha')))
        eq(self.rglob('a**'), self.joins(('a',), ('aaa',), ('aab',)))
        expect = [('a', 'bcd', 'EF'), ('EF',)]
        if can_symlink():
            expect += [('sym3', 'EF')]
        eq(self.rglob('**', 'EF'), self.joins(*expect))
        expect = [('a', 'bcd', 'EF'), ('aaa', 'zzzF'), ('aab', 'F'), ('EF',)]
        if can_symlink():
            expect += [('sym3', 'EF')]
        eq(self.rglob('**', '*F'), self.joins(*expect))
        eq(self.rglob('**', '*F', ''), [])
        eq(self.rglob('**', 'bcd', '*'), self.joins(
            ('a', 'bcd', 'EF'), ('a', 'bcd', 'efg')))
        eq(self.rglob('a', '**', 'bcd'), self.joins(('a', 'bcd')))

        with change_cwd(self.tempdir):
            join = os.path.join
            eq(glob.glob('**', recursive=True), [join(*i) for i in full])
            eq(glob.glob(join('**', ''), recursive=True),
                [join(*i) for i in dirs])
            eq(glob.glob(join('**', '*'), recursive=True),
                [join(*i) for i in full])
            eq(glob.glob(join(os.curdir, '**'), recursive=True),
                [join(os.curdir, '')] + [join(os.curdir, *i) for i in full])
            eq(glob.glob(join(os.curdir, '**', ''), recursive=True),
                [join(os.curdir, '')] + [join(os.curdir, *i) for i in dirs])
            eq(glob.glob(join(os.curdir, '**', '*'), recursive=True),
                [join(os.curdir, *i) for i in full])
            eq(glob.glob(join('**','zz*F'), recursive=True),
                [join('aaa', 'zzzF')])
            eq(glob.glob('**zz*F', recursive=True), [])
            expect = [join('a', 'bcd', 'EF'), 'EF']
            if can_symlink():
                expect += [join('sym3', 'EF')]
            eq(glob.glob(join('**', 'EF'), recursive=True), expect)

            rec = [('.bb','H'), ('.bb','.J'), ('.aa','G'), ('.aa',), ('.bb',)]
            eq(glob.glob('**', recursive=True, include_hidden=True),
               [join(*i) for i in full+rec])