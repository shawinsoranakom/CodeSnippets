def test_exceptions(self):
        badvalue = lambda f: self.assertRaises(ValueError, f)
        badtype = lambda f: self.assertRaises(TypeError, f)

        # Badly formed hex strings.
        badvalue(lambda: self.uuid.UUID(''))
        badvalue(lambda: self.uuid.UUID('abc'))
        badvalue(lambda: self.uuid.UUID('1234567812345678123456781234567'))
        badvalue(lambda: self.uuid.UUID('123456781234567812345678123456789'))
        badvalue(lambda: self.uuid.UUID('123456781234567812345678z2345678'))

        # Badly formed bytes.
        badvalue(lambda: self.uuid.UUID(bytes='abc'))
        badvalue(lambda: self.uuid.UUID(bytes='\0'*15))
        badvalue(lambda: self.uuid.UUID(bytes='\0'*17))

        # Badly formed bytes_le.
        badvalue(lambda: self.uuid.UUID(bytes_le='abc'))
        badvalue(lambda: self.uuid.UUID(bytes_le='\0'*15))
        badvalue(lambda: self.uuid.UUID(bytes_le='\0'*17))

        # Badly formed fields.
        badvalue(lambda: self.uuid.UUID(fields=(1,)))
        badvalue(lambda: self.uuid.UUID(fields=(1, 2, 3, 4, 5)))
        badvalue(lambda: self.uuid.UUID(fields=(1, 2, 3, 4, 5, 6, 7)))

        # Field values out of range.
        badvalue(lambda: self.uuid.UUID(fields=(-1, 0, 0, 0, 0, 0)))
        badvalue(lambda: self.uuid.UUID(fields=(0x100000000, 0, 0, 0, 0, 0)))
        badvalue(lambda: self.uuid.UUID(fields=(0, -1, 0, 0, 0, 0)))
        badvalue(lambda: self.uuid.UUID(fields=(0, 0x10000, 0, 0, 0, 0)))
        badvalue(lambda: self.uuid.UUID(fields=(0, 0, -1, 0, 0, 0)))
        badvalue(lambda: self.uuid.UUID(fields=(0, 0, 0x10000, 0, 0, 0)))
        badvalue(lambda: self.uuid.UUID(fields=(0, 0, 0, -1, 0, 0)))
        badvalue(lambda: self.uuid.UUID(fields=(0, 0, 0, 0x100, 0, 0)))
        badvalue(lambda: self.uuid.UUID(fields=(0, 0, 0, 0, -1, 0)))
        badvalue(lambda: self.uuid.UUID(fields=(0, 0, 0, 0, 0x100, 0)))
        badvalue(lambda: self.uuid.UUID(fields=(0, 0, 0, 0, 0, -1)))
        badvalue(lambda: self.uuid.UUID(fields=(0, 0, 0, 0, 0, 0x1000000000000)))

        # Version number out of range.
        badvalue(lambda: self.uuid.UUID('00'*16, version=0))
        badvalue(lambda: self.uuid.UUID('00'*16, version=42))

        # Integer value out of range.
        badvalue(lambda: self.uuid.UUID(int=-1))
        badvalue(lambda: self.uuid.UUID(int=1<<128))

        # Must supply exactly one of hex, bytes, fields, int.
        h, b, f, i = '00'*16, b'\0'*16, (0, 0, 0, 0, 0, 0), 0
        self.uuid.UUID(h)
        self.uuid.UUID(hex=h)
        self.uuid.UUID(bytes=b)
        self.uuid.UUID(bytes_le=b)
        self.uuid.UUID(fields=f)
        self.uuid.UUID(int=i)

        # Wrong number of arguments (positional).
        badtype(lambda: self.uuid.UUID())
        badtype(lambda: self.uuid.UUID(h, b))
        badtype(lambda: self.uuid.UUID(h, b, b))
        badtype(lambda: self.uuid.UUID(h, b, b, f))
        badtype(lambda: self.uuid.UUID(h, b, b, f, i))

        # Duplicate arguments.
        for hh in [[], [('hex', h)]]:
            for bb in [[], [('bytes', b)]]:
                for bble in [[], [('bytes_le', b)]]:
                    for ii in [[], [('int', i)]]:
                        for ff in [[], [('fields', f)]]:
                            args = dict(hh + bb + bble + ii + ff)
                            if len(args) != 0:
                                badtype(lambda: self.uuid.UUID(h, **args))
                            if len(args) != 1:
                                badtype(lambda: self.uuid.UUID(**args))

        # Immutability.
        u = self.uuid.UUID(h)
        badtype(lambda: setattr(u, 'hex', h))
        badtype(lambda: setattr(u, 'bytes', b))
        badtype(lambda: setattr(u, 'bytes_le', b))
        badtype(lambda: setattr(u, 'fields', f))
        badtype(lambda: setattr(u, 'int', i))
        badtype(lambda: setattr(u, 'time_low', 0))
        badtype(lambda: setattr(u, 'time_mid', 0))
        badtype(lambda: setattr(u, 'time_hi_version', 0))
        badtype(lambda: setattr(u, 'time_hi_version', 0))
        badtype(lambda: setattr(u, 'clock_seq_hi_variant', 0))
        badtype(lambda: setattr(u, 'clock_seq_low', 0))
        badtype(lambda: setattr(u, 'node', 0))

        # Comparison with a non-UUID object
        badtype(lambda: u < object())
        badtype(lambda: u > object())