def test_all_files(self):
        for dirpath, dirnames, filenames in os.walk(rootDir):
            for ignore_dir in IGNORED_DIRS:
                if ignore_dir in dirnames:
                    # If we remove the directory from dirnames os.walk won't
                    # recurse into it
                    dirnames.remove(ignore_dir)
            for basename in filenames:
                if not basename.endswith('.py'):
                    continue
                if basename in IGNORED_FILES:
                    continue

                fn = os.path.join(dirpath, basename)
                with open(fn, encoding='utf-8') as inf:
                    code = inf.read()

                if "'" not in code and '"' not in code:
                    continue
                assertRegexpMatches(
                    self,
                    code,
                    r'(?:(?:#.*?|\s*)\n)*from __future__ import (?:[a-z_]+,\s*)*unicode_literals',
                    'unicode_literals import  missing in %s' % fn)

                m = re.search(r'(?<=\s)u[\'"](?!\)|,|$)', code)
                if m is not None:
                    self.assertTrue(
                        m is None,
                        'u present in %s, around %s' % (
                            fn, code[m.start() - 10:m.end() + 10]))