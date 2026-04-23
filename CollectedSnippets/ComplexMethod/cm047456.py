def test_check_tests(self):
        checker = InitChecker()

        errors = []
        for manifest in Manifest.all_addon_manifests():
            checker.names.clear()
            p = checker.path = pathlib.Path(manifest.path, 'tests')
            if not p.exists():
                continue

            init = p / '__init__.py'
            assert init.exists(), f"Python test directories must have an init, none found in {p}"

            checker.visit(ast.parse(init.read_bytes(), init))

            for f in p.rglob('test_*.py'):
                # special case of a test file which can't be tested normally
                if f.match("odoo/addons/base/tests/test_uninstall.py"):
                    continue
                checker.names[os.fspath(f.relative_to(p))] -= 1

            for test_path, count in checker.names.items():
                match count:
                    case -1:
                        errors.append(f"Test file {test_path} never imported in {init}")
                    case 0:
                        pass
                    case _:
                        errors.append(f"Test file {test_path} imported multiple times in {init}")

        if errors:
            raise AssertionError("Found test errors:" + "".join(f"\n- {e}" for e in errors))