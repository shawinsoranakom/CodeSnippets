def test_serialize_pathlib(self):
        # Pure path objects work in all platforms.
        self.assertSerializedEqual(pathlib.PurePosixPath())
        self.assertSerializedEqual(pathlib.PureWindowsPath())
        path = pathlib.PurePosixPath("/path/file.txt")
        expected = ("pathlib.PurePosixPath('/path/file.txt')", {"import pathlib"})
        self.assertSerializedResultEqual(path, expected)
        path = pathlib.PureWindowsPath("A:\\File.txt")
        expected = ("pathlib.PureWindowsPath('A:/File.txt')", {"import pathlib"})
        self.assertSerializedResultEqual(path, expected)
        # Concrete path objects work on supported platforms.
        if sys.platform == "win32":
            self.assertSerializedEqual(pathlib.WindowsPath.cwd())
            path = pathlib.WindowsPath("A:\\File.txt")
            expected = ("pathlib.PureWindowsPath('A:/File.txt')", {"import pathlib"})
            self.assertSerializedResultEqual(path, expected)
        else:
            self.assertSerializedEqual(pathlib.PosixPath.cwd())
            path = pathlib.PosixPath("/path/file.txt")
            expected = ("pathlib.PurePosixPath('/path/file.txt')", {"import pathlib"})
            self.assertSerializedResultEqual(path, expected)

        field = models.FilePathField(path=pathlib.PurePosixPath("/home/user"))
        string, imports = MigrationWriter.serialize(field)
        self.assertEqual(
            string,
            "models.FilePathField(path=pathlib.PurePosixPath('/home/user'))",
        )
        self.assertIn("import pathlib", imports)