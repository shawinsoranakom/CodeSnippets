def test_basics(self):
        s = "abc123"  # all codecs should be able to encode these
        for encoding in all_unicode_encodings:
            name = codecs.lookup(encoding).name
            if encoding.endswith("_codec"):
                name += "_codec"
            elif encoding == "latin_1":
                name = "latin_1"
            # Skip the mbcs alias on Windows
            if name != "mbcs":
                self.assertEqual(encoding.replace("_", "-"),
                                 name.replace("_", "-"))

            (b, size) = codecs.getencoder(encoding)(s)
            self.assertEqual(size, len(s), "encoding=%r" % encoding)
            (chars, size) = codecs.getdecoder(encoding)(b)
            self.assertEqual(chars, s, "encoding=%r" % encoding)

            if encoding not in broken_unicode_with_stateful:
                # check stream reader/writer
                q = Queue(b"")
                writer = codecs.getwriter(encoding)(q)
                encodedresult = b""
                for c in s:
                    writer.write(c)
                    chunk = q.read()
                    self.assertTrue(type(chunk) is bytes, type(chunk))
                    encodedresult += chunk
                q = Queue(b"")
                reader = codecs.getreader(encoding)(q)
                decodedresult = ""
                for c in encodedresult:
                    q.write(bytes([c]))
                    decodedresult += reader.read()
                self.assertEqual(decodedresult, s, "encoding=%r" % encoding)

            if encoding not in broken_unicode_with_stateful:
                # check incremental decoder/encoder and iterencode()/iterdecode()
                try:
                    encoder = codecs.getincrementalencoder(encoding)()
                except LookupError:  # no IncrementalEncoder
                    pass
                else:
                    # check incremental decoder/encoder
                    encodedresult = b""
                    for c in s:
                        encodedresult += encoder.encode(c)
                    encodedresult += encoder.encode("", True)
                    decoder = codecs.getincrementaldecoder(encoding)()
                    decodedresult = ""
                    for c in encodedresult:
                        decodedresult += decoder.decode(bytes([c]))
                    decodedresult += decoder.decode(b"", True)
                    self.assertEqual(decodedresult, s,
                                     "encoding=%r" % encoding)

                    # check iterencode()/iterdecode()
                    result = "".join(codecs.iterdecode(
                            codecs.iterencode(s, encoding), encoding))
                    self.assertEqual(result, s, "encoding=%r" % encoding)

                    # check iterencode()/iterdecode() with empty string
                    result = "".join(codecs.iterdecode(
                            codecs.iterencode("", encoding), encoding))
                    self.assertEqual(result, "")

                if encoding not in ("idna", "mbcs"):
                    # check incremental decoder/encoder with errors argument
                    try:
                        encoder = codecs.getincrementalencoder(encoding)("ignore")
                    except LookupError:  # no IncrementalEncoder
                        pass
                    else:
                        encodedresult = b"".join(encoder.encode(c) for c in s)
                        decoder = codecs.getincrementaldecoder(encoding)("ignore")
                        decodedresult = "".join(decoder.decode(bytes([c]))
                                                for c in encodedresult)
                        self.assertEqual(decodedresult, s,
                                         "encoding=%r" % encoding)