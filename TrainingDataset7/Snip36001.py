def test_bytecode_conversion_to_source(self):
        """.pyc and .pyo files are included in the files list."""
        filename = self.temporary_file("test_compiled.py")
        filename.touch()
        compiled_file = Path(
            py_compile.compile(str(filename), str(filename.with_suffix(".pyc")))
        )
        filename.unlink()
        with extend_sys_path(str(compiled_file.parent)):
            self.import_and_cleanup("test_compiled")
        self.assertFileFound(compiled_file)