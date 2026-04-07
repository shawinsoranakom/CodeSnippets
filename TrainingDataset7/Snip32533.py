def test_module_import(self):
        relpath = self.hashed_file_path("cached/module.js")
        self.assertEqual(relpath, "cached/module.eaa407b94311.js")
        tests = [
            # Relative imports.
            b'import testConst from "./module_test.477bbebe77f0.js";',
            b'import relativeModule from "../nested/js/nested.866475c46bb4.js";',
            b'import { firstConst, secondConst } from "./module_test.477bbebe77f0.js";',
            # Absolute import.
            b'import rootConst from "/static/absolute_root.5586327fe78c.js";',
            # Dynamic import.
            b'const dynamicModule = import("./module_test.477bbebe77f0.js");',
            # Creating a module object.
            b'import * as NewModule from "./module_test.477bbebe77f0.js";',
            # Creating a minified module object.
            b'import*as m from "./module_test.477bbebe77f0.js";',
            b'import* as m from "./module_test.477bbebe77f0.js";',
            b'import *as m from "./module_test.477bbebe77f0.js";',
            b'import*  as  m from "./module_test.477bbebe77f0.js";',
            # Aliases.
            b'import { testConst as alias } from "./module_test.477bbebe77f0.js";',
            b"import {\n"
            b"    firstVar1 as firstVarAlias,\n"
            b"    $second_var_2 as secondVarAlias\n"
            b'} from "./module_test.477bbebe77f0.js";',
            # Ignore block comments
            b'/* export * from "./module_test_missing.js"; */',
            b"/*\n"
            b'import rootConst from "/static/absolute_root_missing.js";\n'
            b'const dynamicModule = import("./module_test_missing.js");\n'
            b"*/",
            # Ignore line comments
            b'// import testConst from "./module_test_missing.js";',
            b'// const dynamicModule = import("./module_test_missing.js");',
        ]
        with storage.staticfiles_storage.open(relpath) as relfile:
            content = relfile.read()
            for module_import in tests:
                with self.subTest(module_import=module_import):
                    self.assertIn(module_import, content)