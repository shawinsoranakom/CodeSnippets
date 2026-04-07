def test_aggregating_modules(self):
        relpath = self.hashed_file_path("cached/module.js")
        self.assertEqual(relpath, "cached/module.eaa407b94311.js")
        tests = [
            b'export * from "./module_test.477bbebe77f0.js";',
            b'export { testConst } from "./module_test.477bbebe77f0.js";',
            b"export {\n"
            b"    firstVar as firstVarAlias,\n"
            b"    secondVar as secondVarAlias\n"
            b'} from "./module_test.477bbebe77f0.js";',
        ]
        with storage.staticfiles_storage.open(relpath) as relfile:
            content = relfile.read()
            for module_import in tests:
                with self.subTest(module_import=module_import):
                    self.assertIn(module_import, content)