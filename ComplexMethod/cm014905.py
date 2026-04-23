def test_native_functions_yaml(self):
        operators_found = set()
        regex = re.compile(r"^(\w*)(\(|\.)")
        with open(aten_native_yaml) as file:
            for f in yaml.safe_load(file.read()):
                f = f['func']
                ret = f.split('->')[1].strip()
                name = regex.findall(f)[0][0]
                if name in all_operators_with_namedtuple_return :
                    operators_found.add(name)
                    continue
                if '_backward' in name or name.endswith('_forward'):
                    continue
                if not ret.startswith('('):
                    continue
                if ret == '()':
                    continue
                if name in all_operators_with_namedtuple_return_skip_list:
                    continue
                ret = ret[1:-1].split(',')
                for r in ret:
                    r = r.strip()
                    self.assertEqual(len(r.split()), 1, 'only allowlisted '
                                     'operators are allowed to have named '
                                     'return type, got ' + name)
        self.assertEqual(all_operators_with_namedtuple_return, operators_found, textwrap.dedent("""
        Some elements in the `all_operators_with_namedtuple_return` of test_namedtuple_return_api.py
        could not be found. Do you forget to update test_namedtuple_return_api.py after renaming some
        operator?
        """))