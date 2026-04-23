def test_memoryview_cast_1D_ND(self):
        # Cast between C-contiguous buffers. At least one buffer must
        # be 1D, at least one format must be 'c', 'b' or 'B'.
        for _tshape in gencastshapes():
            for char in fmtdict['@']:
                # Casts to _Bool are undefined if the source contains values
                # other than 0 or 1.
                if char == "?":
                    continue
                tfmt = ('', '@')[randrange(2)] + char
                tsize = struct.calcsize(tfmt)
                n = prod(_tshape) * tsize
                obj = 'memoryview' if is_byte_format(tfmt) else 'bytefmt'
                for fmt, items, _ in iter_format(n, obj):
                    size = struct.calcsize(fmt)
                    shape = [n] if n > 0 else []
                    tshape = _tshape + [size]

                    ex = ndarray(items, shape=shape, format=fmt)
                    m = memoryview(ex)

                    titems, tshape = cast_items(ex, tfmt, tsize, shape=tshape)

                    if titems is None:
                        self.assertRaises(TypeError, m.cast, tfmt, tshape)
                        continue
                    if titems == 'nan':
                        continue # NaNs in lists are a recipe for trouble.

                    # 1D -> ND
                    nd = ndarray(titems, shape=tshape, format=tfmt)

                    m2 = m.cast(tfmt, shape=tshape)
                    ndim = len(tshape)
                    strides = nd.strides
                    lst = nd.tolist()
                    self.verify(m2, obj=ex,
                                itemsize=tsize, fmt=tfmt, readonly=True,
                                ndim=ndim, shape=tshape, strides=strides,
                                lst=lst, cast=True)

                    # ND -> 1D
                    m3 = m2.cast(fmt)
                    m4 = m2.cast(fmt, shape=shape)
                    ndim = len(shape)
                    strides = ex.strides
                    lst = ex.tolist()

                    self.verify(m3, obj=ex,
                                itemsize=size, fmt=fmt, readonly=True,
                                ndim=ndim, shape=shape, strides=strides,
                                lst=lst, cast=True)

                    self.verify(m4, obj=ex,
                                itemsize=size, fmt=fmt, readonly=True,
                                ndim=ndim, shape=shape, strides=strides,
                                lst=lst, cast=True)

        if ctypes:
            # format: "T{>l:x:>d:y:}"
            class BEPoint(ctypes.BigEndianStructure):
                _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_double)]
            point = BEPoint(100, 200.1)
            m1 = memoryview(point)
            m2 = m1.cast('B')
            self.assertEqual(m2.obj, point)
            self.assertEqual(m2.itemsize, 1)
            self.assertIs(m2.readonly, False)
            self.assertEqual(m2.ndim, 1)
            self.assertEqual(m2.shape, (m2.nbytes,))
            self.assertEqual(m2.strides, (1,))
            self.assertEqual(m2.suboffsets, ())

            x = ctypes.c_double(1.2)
            m1 = memoryview(x)
            m2 = m1.cast('c')
            self.assertEqual(m2.obj, x)
            self.assertEqual(m2.itemsize, 1)
            self.assertIs(m2.readonly, False)
            self.assertEqual(m2.ndim, 1)
            self.assertEqual(m2.shape, (m2.nbytes,))
            self.assertEqual(m2.strides, (1,))
            self.assertEqual(m2.suboffsets, ())