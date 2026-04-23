def test_utf8_decode_invalid_sequences(self):
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
            self.assertRaises(UnicodeDecodeError, byte.decode, 'utf-8')

        for sb in invalid_2B_seq_start_bytes:
            for cb in continuation_bytes:
                self.assertRaises(UnicodeDecodeError, (sb+cb).decode, 'utf-8')

        for sb in invalid_4B_seq_start_bytes:
            for cb1 in continuation_bytes[:3]:
                for cb3 in continuation_bytes[:3]:
                    self.assertRaises(UnicodeDecodeError,
                                      (sb+cb1+b'\x80'+cb3).decode, 'utf-8')

        for cb in [bytes([x]) for x in range(0x80, 0xA0)]:
            self.assertRaises(UnicodeDecodeError,
                              (b'\xE0'+cb+b'\x80').decode, 'utf-8')
            self.assertRaises(UnicodeDecodeError,
                              (b'\xE0'+cb+b'\xBF').decode, 'utf-8')
        # surrogates
        for cb in [bytes([x]) for x in range(0xA0, 0xC0)]:
            self.assertRaises(UnicodeDecodeError,
                              (b'\xED'+cb+b'\x80').decode, 'utf-8')
            self.assertRaises(UnicodeDecodeError,
                              (b'\xED'+cb+b'\xBF').decode, 'utf-8')
        for cb in [bytes([x]) for x in range(0x80, 0x90)]:
            self.assertRaises(UnicodeDecodeError,
                              (b'\xF0'+cb+b'\x80\x80').decode, 'utf-8')
            self.assertRaises(UnicodeDecodeError,
                              (b'\xF0'+cb+b'\xBF\xBF').decode, 'utf-8')
        for cb in [bytes([x]) for x in range(0x90, 0xC0)]:
            self.assertRaises(UnicodeDecodeError,
                              (b'\xF4'+cb+b'\x80\x80').decode, 'utf-8')
            self.assertRaises(UnicodeDecodeError,
                              (b'\xF4'+cb+b'\xBF\xBF').decode, 'utf-8')