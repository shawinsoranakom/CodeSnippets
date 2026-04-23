def test_reverse_import_mapping(self):
        for module2, module3 in IMPORT_MAPPING.items():
            with self.subTest((module2, module3)):
                try:
                    getmodule(module3)
                except ImportError as exc:
                    if support.verbose:
                        print(exc)
                if ((module2, module3) not in ALT_IMPORT_MAPPING and
                    REVERSE_IMPORT_MAPPING.get(module3, None) != module2):
                    for (m3, n3), (m2, n2) in REVERSE_NAME_MAPPING.items():
                        if (module3, module2) == (m3, m2):
                            break
                    else:
                        self.fail('No reverse mapping from %r to %r' %
                                  (module3, module2))
                module = REVERSE_IMPORT_MAPPING.get(module3, module3)
                module = IMPORT_MAPPING.get(module, module)
                self.assertEqual(module, module3)