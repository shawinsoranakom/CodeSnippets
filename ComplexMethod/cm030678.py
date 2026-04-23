def test_pythonmalloc(self):
        # Test the PYTHONMALLOC environment variable
        malloc = not support.Py_GIL_DISABLED
        pymalloc = support.with_pymalloc()
        mimalloc = support.with_mimalloc()
        if support.Py_GIL_DISABLED:
            default_name = 'mimalloc_debug' if support.Py_DEBUG else 'mimalloc'
            default_name_debug = 'mimalloc_debug'
        elif pymalloc:
            default_name = 'pymalloc_debug' if support.Py_DEBUG else 'pymalloc'
            default_name_debug = 'pymalloc_debug'
        else:
            default_name = 'malloc_debug' if support.Py_DEBUG else 'malloc'
            default_name_debug = 'malloc_debug'

        tests = [
            (None, default_name),
            ('debug', default_name_debug),
        ]
        if malloc:
            tests.extend([
                ('malloc', 'malloc'),
                ('malloc_debug', 'malloc_debug'),
            ])
        if pymalloc:
            tests.extend((
                ('pymalloc', 'pymalloc'),
                ('pymalloc_debug', 'pymalloc_debug'),
            ))
        if mimalloc:
            tests.extend((
                ('mimalloc', 'mimalloc'),
                ('mimalloc_debug', 'mimalloc_debug'),
            ))

        for env_var, name in tests:
            with self.subTest(env_var=env_var, name=name):
                self.check_pythonmalloc(env_var, name)