def test_attributes(self):
        self.assertIsInstance(sys.api_version, int)
        self.assertIsInstance(sys.argv, list)
        for arg in sys.argv:
            self.assertIsInstance(arg, str)
        self.assertIsInstance(sys.orig_argv, list)
        for arg in sys.orig_argv:
            self.assertIsInstance(arg, str)
        self.assertIn(sys.byteorder, ("little", "big"))
        self.assertIsInstance(sys.builtin_module_names, tuple)
        self.assertIsInstance(sys.copyright, str)
        self.assertIsInstance(sys.exec_prefix, str)
        self.assertIsInstance(sys.base_exec_prefix, str)
        self.assertIsInstance(sys.executable, str)
        self.assertEqual(len(sys.float_info), 11)
        self.assertEqual(sys.float_info.radix, 2)
        self.assertEqual(len(sys.int_info), 4)
        self.assertTrue(sys.int_info.bits_per_digit % 5 == 0)
        self.assertTrue(sys.int_info.sizeof_digit >= 1)
        self.assertGreaterEqual(sys.int_info.default_max_str_digits, 500)
        self.assertGreaterEqual(sys.int_info.str_digits_check_threshold, 100)
        self.assertGreater(sys.int_info.default_max_str_digits,
                           sys.int_info.str_digits_check_threshold)
        self.assertEqual(type(sys.int_info.bits_per_digit), int)
        self.assertEqual(type(sys.int_info.sizeof_digit), int)
        self.assertIsInstance(sys.int_info.default_max_str_digits, int)
        self.assertIsInstance(sys.int_info.str_digits_check_threshold, int)
        self.assertIsInstance(sys.hexversion, int)

        self.assertEqual(len(sys.hash_info), 9)
        self.assertLess(sys.hash_info.modulus, 2**sys.hash_info.width)
        # sys.hash_info.modulus should be a prime; we do a quick
        # probable primality test (doesn't exclude the possibility of
        # a Carmichael number)
        for x in range(1, 100):
            self.assertEqual(
                pow(x, sys.hash_info.modulus-1, sys.hash_info.modulus),
                1,
                "sys.hash_info.modulus {} is a non-prime".format(
                    sys.hash_info.modulus)
                )
        self.assertIsInstance(sys.hash_info.inf, int)
        self.assertIsInstance(sys.hash_info.nan, int)
        self.assertIsInstance(sys.hash_info.imag, int)
        algo = sysconfig.get_config_var("Py_HASH_ALGORITHM")
        if sys.hash_info.algorithm in {"fnv", "siphash13", "siphash24"}:
            self.assertIn(sys.hash_info.hash_bits, {32, 64})
            self.assertIn(sys.hash_info.seed_bits, {32, 64, 128})

            if algo == 1:
                self.assertEqual(sys.hash_info.algorithm, "siphash24")
            elif algo == 2:
                self.assertEqual(sys.hash_info.algorithm, "fnv")
            elif algo == 3:
                self.assertEqual(sys.hash_info.algorithm, "siphash13")
            else:
                self.assertIn(sys.hash_info.algorithm, {"fnv", "siphash13", "siphash24"})
        else:
            # PY_HASH_EXTERNAL
            self.assertEqual(algo, 0)
        self.assertGreaterEqual(sys.hash_info.cutoff, 0)
        self.assertLess(sys.hash_info.cutoff, 8)

        self.assertIsInstance(sys.maxsize, int)
        self.assertIsInstance(sys.maxunicode, int)
        self.assertEqual(sys.maxunicode, 0x10FFFF)
        self.assertIsInstance(sys.platform, str)
        self.assertIsInstance(sys.prefix, str)
        self.assertIsInstance(sys.base_prefix, str)
        self.assertIsInstance(sys.platlibdir, str)
        self.assertIsInstance(sys.version, str)
        vi = sys.version_info
        self.assertIsInstance(vi[:], tuple)
        self.assertEqual(len(vi), 5)
        self.assertIsInstance(vi[0], int)
        self.assertIsInstance(vi[1], int)
        self.assertIsInstance(vi[2], int)
        self.assertIn(vi[3], ("alpha", "beta", "candidate", "final"))
        self.assertIsInstance(vi[4], int)
        self.assertIsInstance(vi.major, int)
        self.assertIsInstance(vi.minor, int)
        self.assertIsInstance(vi.micro, int)
        self.assertIn(vi.releaselevel, ("alpha", "beta", "candidate", "final"))
        self.assertIsInstance(vi.serial, int)
        self.assertEqual(vi[0], vi.major)
        self.assertEqual(vi[1], vi.minor)
        self.assertEqual(vi[2], vi.micro)
        self.assertEqual(vi[3], vi.releaselevel)
        self.assertEqual(vi[4], vi.serial)
        self.assertTrue(vi > (1,0,0))
        self.assertIsInstance(sys.float_repr_style, str)
        self.assertIn(sys.float_repr_style, ('short', 'legacy'))
        if not sys.platform.startswith('win'):
            self.assertIsInstance(sys.abiflags, str)