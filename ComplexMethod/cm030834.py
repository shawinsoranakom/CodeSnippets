def test_oob_buffers(self):
        # Test out-of-band buffers (PEP 574)
        for obj in self.buffer_like_objects():
            for proto in range(0, 5):
                # Need protocol >= 5 for buffer_callback
                with self.assertRaises(ValueError):
                    self.dumps(obj, proto,
                               buffer_callback=[].append)
            for proto in range(5, pickle.HIGHEST_PROTOCOL + 1):
                buffers = []
                buffer_callback = lambda pb: buffers.append(pb.raw())
                data = self.dumps(obj, proto,
                                  buffer_callback=buffer_callback)
                self.assertNotIn(b"abcdefgh", data)
                self.assertEqual(count_opcode(pickle.SHORT_BINBYTES, data), 0)
                self.assertEqual(count_opcode(pickle.BYTEARRAY8, data), 0)
                self.assertEqual(count_opcode(pickle.NEXT_BUFFER, data), 1)
                self.assertEqual(count_opcode(pickle.READONLY_BUFFER, data),
                                 1 if obj.readonly else 0)

                if obj.c_contiguous:
                    self.assertEqual(bytes(buffers[0]), b"abcdefgh")
                # Need buffers argument to unpickle properly
                with self.assertRaises(pickle.UnpicklingError):
                    self.loads(data)

                new = self.loads(data, buffers=buffers)
                if obj.zero_copy_reconstruct:
                    # Zero-copy achieved
                    self.assertIs(new, obj)
                else:
                    self.assertIs(type(new), type(obj))
                    self.assertEqual(new, obj)
                # Non-sequence buffers accepted too
                new = self.loads(data, buffers=iter(buffers))
                if obj.zero_copy_reconstruct:
                    # Zero-copy achieved
                    self.assertIs(new, obj)
                else:
                    self.assertIs(type(new), type(obj))
                    self.assertEqual(new, obj)