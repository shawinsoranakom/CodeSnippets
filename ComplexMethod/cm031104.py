def test_field_descriptor_attributes(self):
        """Test information provided by the descriptors"""
        class Inner(Structure):
            _fields_ = [
                ("a", c_int16),
                ("b", c_int8, 1),
                ("c", c_int8, 2),
            ]
        class X(self.cls):
            _fields_ = [
                ("x", c_int32),
                ("y", c_int16, 1),
                ("_", Inner),
            ]
            _anonymous_ = ["_"]

        field_names = "xy_abc"

        # name

        for name in field_names:
            with self.subTest(name=name):
                self.assertEqual(getattr(X, name).name, name)

        # type

        expected_types = dict(
            x=c_int32,
            y=c_int16,
            _=Inner,
            a=c_int16,
            b=c_int8,
            c=c_int8,
        )
        assert set(expected_types) == set(field_names)
        for name, tp in expected_types.items():
            with self.subTest(name=name):
                self.assertEqual(getattr(X, name).type, tp)
                self.assertEqual(getattr(X, name).byte_size, sizeof(tp))

        # offset, byte_offset

        expected_offsets = dict(
            x=(0, 0),
            y=(0, 4),
            _=(0, 6),
            a=(0, 6),
            b=(2, 8),
            c=(2, 8),
        )
        assert set(expected_offsets) == set(field_names)
        for name, (union_offset, struct_offset) in expected_offsets.items():
            with self.subTest(name=name):
                self.assertEqual(getattr(X, name).offset,
                                 getattr(X, name).byte_offset)
                if self.cls == Structure:
                    self.assertEqual(getattr(X, name).offset, struct_offset)
                else:
                    self.assertEqual(getattr(X, name).offset, union_offset)

        # is_bitfield, bit_size, bit_offset
        # size

        little_endian = (sys.byteorder == 'little')
        expected_bitfield_info = dict(
            # (bit_size, bit_offset)
            b=(1, 0 if little_endian else 7),
            c=(2, 1 if little_endian else 5),
            y=(1, 0 if little_endian else 15),
        )
        for name in field_names:
            with self.subTest(name=name):
                if info := expected_bitfield_info.get(name):
                    self.assertEqual(getattr(X, name).is_bitfield, True)
                    expected_bit_size, expected_bit_offset = info
                    self.assertEqual(getattr(X, name).bit_size,
                                     expected_bit_size)
                    self.assertEqual(getattr(X, name).bit_offset,
                                     expected_bit_offset)
                    self.assertEqual(getattr(X, name).size,
                                     (expected_bit_size << 16)
                                     | expected_bit_offset)
                else:
                    self.assertEqual(getattr(X, name).is_bitfield, False)
                    type_size = sizeof(expected_types[name])
                    self.assertEqual(getattr(X, name).bit_size, type_size * 8)
                    self.assertEqual(getattr(X, name).bit_offset, 0)
                    self.assertEqual(getattr(X, name).size, type_size)

        # is_anonymous

        for name in field_names:
            with self.subTest(name=name):
                self.assertEqual(getattr(X, name).is_anonymous, (name == '_'))