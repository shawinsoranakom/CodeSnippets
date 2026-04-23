def check_decode_strings(self, errors):
        is_utf8 = (self.ENCODING == "utf-8")
        if is_utf8:
            encode_errors = 'surrogateescape'
        else:
            encode_errors = 'strict'

        strings = list(self.BYTES_STRINGS)
        for text in self.STRINGS:
            try:
                encoded = text.encode(self.ENCODING, encode_errors)
                if encoded not in strings:
                    strings.append(encoded)
            except UnicodeEncodeError:
                encoded = None

            if is_utf8:
                encoded2 = text.encode(self.ENCODING, 'surrogatepass')
                if encoded2 != encoded:
                    strings.append(encoded2)

        for encoded in strings:
            with self.subTest(encoded=encoded):
                try:
                    expected = encoded.decode(self.ENCODING, errors)
                except UnicodeDecodeError:
                    with self.assertRaises(RuntimeError) as cm:
                        self.decode(encoded, errors)
                    errmsg = str(cm.exception)
                    self.assertStartsWith(errmsg, "decode error: ")
                else:
                    decoded = self.decode(encoded, errors)
                    self.assertEqual(decoded, expected)