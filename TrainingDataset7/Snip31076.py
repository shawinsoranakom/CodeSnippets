def test_limited_stream(self):
        # Read all of a limited stream
        stream = LimitedStream(BytesIO(b"test"), 2)
        self.assertEqual(stream.read(), b"te")
        # Reading again returns nothing.
        self.assertEqual(stream.read(), b"")

        # Read a number of characters greater than the stream has to offer
        stream = LimitedStream(BytesIO(b"test"), 2)
        self.assertEqual(stream.read(5), b"te")
        # Reading again returns nothing.
        self.assertEqual(stream.readline(5), b"")

        # Read sequentially from a stream
        stream = LimitedStream(BytesIO(b"12345678"), 8)
        self.assertEqual(stream.read(5), b"12345")
        self.assertEqual(stream.read(5), b"678")
        # Reading again returns nothing.
        self.assertEqual(stream.readline(5), b"")

        # Read lines from a stream
        stream = LimitedStream(BytesIO(b"1234\n5678\nabcd\nefgh\nijkl"), 24)
        # Read a full line, unconditionally
        self.assertEqual(stream.readline(), b"1234\n")
        # Read a number of characters less than a line
        self.assertEqual(stream.readline(2), b"56")
        # Read the rest of the partial line
        self.assertEqual(stream.readline(), b"78\n")
        # Read a full line, with a character limit greater than the line length
        self.assertEqual(stream.readline(6), b"abcd\n")
        # Read the next line, deliberately terminated at the line end
        self.assertEqual(stream.readline(4), b"efgh")
        # Read the next line... just the line end
        self.assertEqual(stream.readline(), b"\n")
        # Read everything else.
        self.assertEqual(stream.readline(), b"ijkl")

        # Regression for #15018
        # If a stream contains a newline, but the provided length
        # is less than the number of provided characters, the newline
        # doesn't reset the available character count
        stream = LimitedStream(BytesIO(b"1234\nabcdef"), 9)
        self.assertEqual(stream.readline(10), b"1234\n")
        self.assertEqual(stream.readline(3), b"abc")
        # Now expire the available characters
        self.assertEqual(stream.readline(3), b"d")
        # Reading again returns nothing.
        self.assertEqual(stream.readline(2), b"")

        # Same test, but with read, not readline.
        stream = LimitedStream(BytesIO(b"1234\nabcdef"), 9)
        self.assertEqual(stream.read(6), b"1234\na")
        self.assertEqual(stream.read(2), b"bc")
        self.assertEqual(stream.read(2), b"d")
        self.assertEqual(stream.read(2), b"")
        self.assertEqual(stream.read(), b"")