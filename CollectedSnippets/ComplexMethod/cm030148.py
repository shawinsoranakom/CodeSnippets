def __init__(self, hex=None, bytes=None, bytes_le=None, fields=None,
                       int=None, version=None,
                       *, is_safe=SafeUUID.unknown):
        r"""Create a UUID from either a string of 32 hexadecimal digits,
        a string of 16 bytes as the 'bytes' argument, a string of 16 bytes
        in little-endian order as the 'bytes_le' argument, a tuple of six
        integers (32-bit time_low, 16-bit time_mid, 16-bit time_hi_version,
        8-bit clock_seq_hi_variant, 8-bit clock_seq_low, 48-bit node) as
        the 'fields' argument, or a single 128-bit integer as the 'int'
        argument.  When a string of hex digits is given, curly braces,
        hyphens, and a URN prefix are all optional.  For example, these
        expressions all yield the same UUID:

        UUID('{12345678-1234-5678-1234-567812345678}')
        UUID('12345678123456781234567812345678')
        UUID('urn:uuid:12345678-1234-5678-1234-567812345678')
        UUID(bytes='\x12\x34\x56\x78'*4)
        UUID(bytes_le='\x78\x56\x34\x12\x34\x12\x78\x56' +
                      '\x12\x34\x56\x78\x12\x34\x56\x78')
        UUID(fields=(0x12345678, 0x1234, 0x5678, 0x12, 0x34, 0x567812345678))
        UUID(int=0x12345678123456781234567812345678)

        Exactly one of 'hex', 'bytes', 'bytes_le', 'fields', or 'int' must
        be given.  The 'version' argument is optional; if given, the resulting
        UUID will have its variant and version set according to RFC 4122,
        overriding the given 'hex', 'bytes', 'bytes_le', 'fields', or 'int'.

        is_safe is an enum exposed as an attribute on the instance.  It
        indicates whether the UUID has been generated in a way that is safe
        for multiprocessing applications, via uuid_generate_time_safe(3).
        """

        if [hex, bytes, bytes_le, fields, int].count(None) != 4:
            raise TypeError('one of the hex, bytes, bytes_le, fields, '
                            'or int arguments must be given')
        if int is not None:
            pass
        elif hex is not None:
            hex = hex.replace('urn:', '').replace('uuid:', '')
            hex = hex.strip('{}').replace('-', '')
            if len(hex) != 32:
                raise ValueError('badly formed hexadecimal UUID string')
            int = int_(hex, 16)
        elif bytes_le is not None:
            if len(bytes_le) != 16:
                raise ValueError('bytes_le is not a 16-char string')
            assert isinstance(bytes_le, bytes_), repr(bytes_le)
            bytes = (bytes_le[4-1::-1] + bytes_le[6-1:4-1:-1] +
                     bytes_le[8-1:6-1:-1] + bytes_le[8:])
            int = int_.from_bytes(bytes)  # big endian
        elif bytes is not None:
            if len(bytes) != 16:
                raise ValueError('bytes is not a 16-char string')
            assert isinstance(bytes, bytes_), repr(bytes)
            int = int_.from_bytes(bytes)  # big endian
        elif fields is not None:
            if len(fields) != 6:
                raise ValueError('fields is not a 6-tuple')
            (time_low, time_mid, time_hi_version,
             clock_seq_hi_variant, clock_seq_low, node) = fields
            if not 0 <= time_low < (1 << 32):
                raise ValueError('field 1 out of range (need a 32-bit value)')
            if not 0 <= time_mid < (1 << 16):
                raise ValueError('field 2 out of range (need a 16-bit value)')
            if not 0 <= time_hi_version < (1 << 16):
                raise ValueError('field 3 out of range (need a 16-bit value)')
            if not 0 <= clock_seq_hi_variant < (1 << 8):
                raise ValueError('field 4 out of range (need an 8-bit value)')
            if not 0 <= clock_seq_low < (1 << 8):
                raise ValueError('field 5 out of range (need an 8-bit value)')
            if not 0 <= node < (1 << 48):
                raise ValueError('field 6 out of range (need a 48-bit value)')
            clock_seq = (clock_seq_hi_variant << 8) | clock_seq_low
            int = ((time_low << 96) | (time_mid << 80) |
                   (time_hi_version << 64) | (clock_seq << 48) | node)
        if not 0 <= int <= _UINT_128_MAX:
            raise ValueError('int is out of range (need a 128-bit value)')
        if version is not None:
            if not 1 <= version <= 8:
                raise ValueError('illegal version number')
            # clear the variant and the version number bits
            int &= _RFC_4122_CLEARFLAGS_MASK
            # Set the variant to RFC 4122/9562.
            int |= 0x8000_0000_0000_0000  # (0x8000 << 48)
            # Set the version number.
            int |= version << 76
        object.__setattr__(self, 'int', int)
        object.__setattr__(self, 'is_safe', is_safe)