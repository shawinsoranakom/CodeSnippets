def test_set_name(self):
        # Ensure main thread name is restored after test
        self.addCleanup(_thread.set_name, _thread._get_name())

        # set_name() limit in bytes
        truncate = getattr(_thread, "_NAME_MAXLEN", None)
        limit = truncate or 100

        tests = [
            # test short ASCII name
            "CustomName",

            # test short non-ASCII name
            "namé€",

            # embedded null character: name is truncated
            # at the first null character
            "embed\0null",

            # Test long ASCII names (not truncated)
            "x" * limit,

            # Test long ASCII names (truncated)
            "x" * (limit + 10),

            # Test long non-ASCII name (truncated)
            "x" * (limit - 1) + "é€",

            # Test long non-BMP names (truncated) creating surrogate pairs
            # on Windows
            "x" * (limit - 1) + "\U0010FFFF",
            "x" * (limit - 2) + "\U0010FFFF" * 2,
            "x" + "\U0001f40d" * limit,
            "xx" + "\U0001f40d" * limit,
            "xxx" + "\U0001f40d" * limit,
            "xxxx" + "\U0001f40d" * limit,
        ]
        if os_helper.FS_NONASCII:
            tests.append(f"nonascii:{os_helper.FS_NONASCII}")
        if os_helper.TESTFN_UNENCODABLE:
            tests.append(os_helper.TESTFN_UNENCODABLE)

        if sys.platform.startswith("sunos"):
            # Use ASCII encoding on Solaris/Illumos/OpenIndiana
            encoding = "ascii"
        else:
            encoding = sys.getfilesystemencoding()

        def work():
            nonlocal work_name
            work_name = _thread._get_name()

        for name in tests:
            if not support.MS_WINDOWS:
                encoded = name.encode(encoding, "replace")
                if b'\0' in encoded:
                    encoded = encoded.split(b'\0', 1)[0]
                if truncate is not None:
                    encoded = encoded[:truncate]
                if sys.platform.startswith("sunos"):
                    expected = encoded.decode("ascii", "surrogateescape")
                else:
                    expected = os.fsdecode(encoded)
            else:
                size = 0
                chars = []
                for ch in name:
                    if ord(ch) > 0xFFFF:
                        size += 2
                    else:
                        size += 1
                    if size > truncate:
                        break
                    chars.append(ch)
                expected = ''.join(chars)

                if '\0' in expected:
                    expected = expected.split('\0', 1)[0]

            with self.subTest(name=name, expected=expected, thread="main"):
                _thread.set_name(name)
                self.assertEqual(_thread._get_name(), expected)

            with self.subTest(name=name, expected=expected, thread="worker"):
                work_name = None
                thread = threading.Thread(target=work, name=name)
                thread.start()
                thread.join()
                self.assertEqual(work_name, expected,
                                 f"{len(work_name)=} and {len(expected)=}")