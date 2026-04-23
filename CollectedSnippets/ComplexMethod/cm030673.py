def test_basics_capi(self):
        s = "abc123"  # all codecs should be able to encode these
        for encoding in all_unicode_encodings:
            if encoding not in broken_unicode_with_stateful:
                # check incremental decoder/encoder (fetched via the C API)
                try:
                    cencoder = _testlimitedcapi.codec_incrementalencoder(encoding)
                except LookupError:  # no IncrementalEncoder
                    pass
                else:
                    # check C API
                    encodedresult = b""
                    for c in s:
                        encodedresult += cencoder.encode(c)
                    encodedresult += cencoder.encode("", True)
                    cdecoder = _testlimitedcapi.codec_incrementaldecoder(encoding)
                    decodedresult = ""
                    for c in encodedresult:
                        decodedresult += cdecoder.decode(bytes([c]))
                    decodedresult += cdecoder.decode(b"", True)
                    self.assertEqual(decodedresult, s,
                                     "encoding=%r" % encoding)

                if encoding not in ("idna", "mbcs"):
                    # check incremental decoder/encoder with errors argument
                    try:
                        cencoder = _testlimitedcapi.codec_incrementalencoder(encoding, "ignore")
                    except LookupError:  # no IncrementalEncoder
                        pass
                    else:
                        encodedresult = b"".join(cencoder.encode(c) for c in s)
                        cdecoder = _testlimitedcapi.codec_incrementaldecoder(encoding, "ignore")
                        decodedresult = "".join(cdecoder.decode(bytes([c]))
                                                for c in encodedresult)
                        self.assertEqual(decodedresult, s,
                                         "encoding=%r" % encoding)