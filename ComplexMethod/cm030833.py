def test_in_band_buffers(self):
        # Test in-band buffers (PEP 574)
        for obj in self.buffer_like_objects():
            for proto in range(0, pickle.HIGHEST_PROTOCOL + 1):
                data = self.dumps(obj, proto)
                if obj.c_contiguous and proto >= 5:
                    # The raw memory bytes are serialized in physical order
                    self.assertIn(b"abcdefgh", data)
                self.assertEqual(count_opcode(pickle.NEXT_BUFFER, data), 0)
                if proto >= 5:
                    self.assertEqual(count_opcode(pickle.SHORT_BINBYTES, data),
                                     1 if obj.readonly else 0)
                    self.assertEqual(count_opcode(pickle.BYTEARRAY8, data),
                                     0 if obj.readonly else 1)
                    # Return a true value from buffer_callback should have
                    # the same effect
                    def buffer_callback(obj):
                        return True
                    data2 = self.dumps(obj, proto,
                                       buffer_callback=buffer_callback)
                    self.assertEqual(data2, data)

                new = self.loads(data)
                # It's a copy
                self.assertIsNot(new, obj)
                self.assertIs(type(new), type(obj))
                self.assertEqual(new, obj)