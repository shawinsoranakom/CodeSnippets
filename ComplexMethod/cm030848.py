def test_invalid_utf8(self):
        # This is a port of test_utf8_decode_invalid_sequences in
        # test_unicode.py to exercise the separate utf8 validator in
        # Parser/tokenizer/helpers.c used when reading source files.

        # That file is written using low-level C file I/O, so the only way to
        # test it is to write actual files to disk.

        # Each example is put inside a string at the top of the file so
        # it's an otherwise valid Python source file. Put some newlines
        # beforehand so we can assert that the error is reported on the
        # correct line.
        template = b'\n\n\n"%s"\n'

        fn = TESTFN
        self.addCleanup(unlink, fn)

        def check(content):
            with open(fn, 'wb') as fp:
                fp.write(template % content)
            rc, stdout, stderr = script_helper.assert_python_failure(fn)
            # We want to assert that the python subprocess failed gracefully,
            # not via a signal.
            self.assertGreaterEqual(rc, 1)
            self.assertIn(b"Non-UTF-8 code starting with", stderr)
            self.assertIn(b"on line 4", stderr)

        # continuation bytes in a sequence of 2, 3, or 4 bytes
        continuation_bytes = [bytes([x]) for x in range(0x80, 0xC0)]
        # start bytes of a 2-byte sequence equivalent to code points < 0x7F
        invalid_2B_seq_start_bytes = [bytes([x]) for x in range(0xC0, 0xC2)]
        # start bytes of a 4-byte sequence equivalent to code points > 0x10FFFF
        invalid_4B_seq_start_bytes = [bytes([x]) for x in range(0xF5, 0xF8)]
        invalid_start_bytes = (
            continuation_bytes + invalid_2B_seq_start_bytes +
            invalid_4B_seq_start_bytes + [bytes([x]) for x in range(0xF7, 0x100)]
        )

        for byte in invalid_start_bytes:
            check(byte)

        for sb in invalid_2B_seq_start_bytes:
            for cb in continuation_bytes:
                check(sb + cb)

        for sb in invalid_4B_seq_start_bytes:
            for cb1 in continuation_bytes[:3]:
                for cb3 in continuation_bytes[:3]:
                    check(sb+cb1+b'\x80'+cb3)

        for cb in [bytes([x]) for x in range(0x80, 0xA0)]:
            check(b'\xE0'+cb+b'\x80')
            check(b'\xE0'+cb+b'\xBF')
            # surrogates
        for cb in [bytes([x]) for x in range(0xA0, 0xC0)]:
            check(b'\xED'+cb+b'\x80')
            check(b'\xED'+cb+b'\xBF')
        for cb in [bytes([x]) for x in range(0x80, 0x90)]:
            check(b'\xF0'+cb+b'\x80\x80')
            check(b'\xF0'+cb+b'\xBF\xBF')
        for cb in [bytes([x]) for x in range(0x90, 0xC0)]:
            check(b'\xF4'+cb+b'\x80\x80')
            check(b'\xF4'+cb+b'\xBF\xBF')