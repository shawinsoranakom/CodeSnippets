def verify(self, result, *, obj,
                     itemsize, fmt, readonly,
                     ndim, shape, strides,
                     lst, sliced=False, cast=False):
        # Verify buffer contents against expected values.
        if shape:
            expected_len = prod(shape)*itemsize
        else:
            if not fmt: # array has been implicitly cast to unsigned bytes
                expected_len = len(lst)
            else: # ndim = 0
                expected_len = itemsize

        # Reconstruct suboffsets from strides. Support for slicing
        # could be added, but is currently only needed for test_getbuf().
        suboffsets = ()
        if result.suboffsets:
            self.assertGreater(ndim, 0)

            suboffset0 = 0
            for n in range(1, ndim):
                if shape[n] == 0:
                    break
                if strides[n] <= 0:
                    suboffset0 += -strides[n] * (shape[n]-1)

            suboffsets = [suboffset0] + [-1 for v in range(ndim-1)]

            # Not correct if slicing has occurred in the first dimension.
            stride0 = self.sizeof_void_p
            if strides[0] < 0:
                stride0 = -stride0
            strides = [stride0] + list(strides[1:])

        self.assertIs(result.obj, obj)
        self.assertEqual(result.nbytes, expected_len)
        self.assertEqual(result.itemsize, itemsize)
        self.assertEqual(result.format, fmt)
        self.assertIs(result.readonly, readonly)
        self.assertEqual(result.ndim, ndim)
        self.assertEqual(result.shape, tuple(shape))
        if not (sliced and suboffsets):
            self.assertEqual(result.strides, tuple(strides))
        self.assertEqual(result.suboffsets, tuple(suboffsets))

        if isinstance(result, ndarray) or is_memoryview_format(fmt):
            rep = result.tolist() if fmt else result.tobytes()
            self.assertEqual(rep, lst)

        if not fmt: # array has been cast to unsigned bytes,
            return  # the remaining tests won't work.

        # PyBuffer_GetPointer() is the definition how to access an item.
        # If PyBuffer_GetPointer(indices) is correct for all possible
        # combinations of indices, the buffer is correct.
        #
        # Also test tobytes() against the flattened 'lst', with all items
        # packed to bytes.
        if not cast: # casts chop up 'lst' in different ways
            b = bytearray()
            buf_err = None
            for ind in indices(shape):
                try:
                    item1 = get_pointer(result, ind)
                    item2 = get_item(lst, ind)
                    if isinstance(item2, tuple):
                        x = struct.pack(fmt, *item2)
                    else:
                        x = struct.pack(fmt, item2)
                    b.extend(x)
                except BufferError:
                    buf_err = True # re-exporter does not provide full buffer
                    break
                self.assertEqual(item1, item2)

            if not buf_err:
                # test tobytes()
                self.assertEqual(result.tobytes(), b)

                # test hex()
                m = memoryview(result)
                h = "".join("%02x" % c for c in b)
                self.assertEqual(m.hex(), h)

                # lst := expected multi-dimensional logical representation
                # flatten(lst) := elements in C-order
                ff = fmt if fmt else 'B'
                flattened = flatten(lst)

                # Rules for 'A': if the array is already contiguous, return
                # the array unaltered. Otherwise, return a contiguous 'C'
                # representation.
                for order in ['C', 'F', 'A']:
                    expected = result
                    if order == 'F':
                        if not is_contiguous(result, 'A') or \
                           is_contiguous(result, 'C'):
                            # For constructing the ndarray, convert the
                            # flattened logical representation to Fortran order.
                            trans = transpose(flattened, shape)
                            expected = ndarray(trans, shape=shape, format=ff,
                                               flags=ND_FORTRAN)
                    else: # 'C', 'A'
                        if not is_contiguous(result, 'A') or \
                           is_contiguous(result, 'F') and order == 'C':
                            # The flattened list is already in C-order.
                            expected = ndarray(flattened, shape=shape, format=ff)

                    contig = get_contiguous(result, PyBUF_READ, order)
                    self.assertEqual(contig.tobytes(), b)
                    self.assertTrue(cmp_contig(contig, expected))

                    if ndim == 0:
                        continue

                    nmemb = len(flattened)
                    ro = 0 if readonly else ND_WRITABLE

                    ### See comment in test_py_buffer_to_contiguous for an
                    ### explanation why these tests are valid.

                    # To 'C'
                    contig = py_buffer_to_contiguous(result, 'C', PyBUF_FULL_RO)
                    self.assertEqual(len(contig), nmemb * itemsize)
                    initlst = [struct.unpack_from(fmt, contig, n*itemsize)
                               for n in range(nmemb)]
                    if len(initlst[0]) == 1:
                        initlst = [v[0] for v in initlst]

                    y = ndarray(initlst, shape=shape, flags=ro, format=fmt)
                    self.assertEqual(memoryview(y), memoryview(result))

                    contig_bytes = memoryview(result).tobytes()
                    self.assertEqual(contig_bytes, contig)

                    contig_bytes = memoryview(result).tobytes(order=None)
                    self.assertEqual(contig_bytes, contig)

                    contig_bytes = memoryview(result).tobytes(order='C')
                    self.assertEqual(contig_bytes, contig)

                    # To 'F'
                    contig = py_buffer_to_contiguous(result, 'F', PyBUF_FULL_RO)
                    self.assertEqual(len(contig), nmemb * itemsize)
                    initlst = [struct.unpack_from(fmt, contig, n*itemsize)
                               for n in range(nmemb)]
                    if len(initlst[0]) == 1:
                        initlst = [v[0] for v in initlst]

                    y = ndarray(initlst, shape=shape, flags=ro|ND_FORTRAN,
                                format=fmt)
                    self.assertEqual(memoryview(y), memoryview(result))

                    contig_bytes = memoryview(result).tobytes(order='F')
                    self.assertEqual(contig_bytes, contig)

                    # To 'A'
                    contig = py_buffer_to_contiguous(result, 'A', PyBUF_FULL_RO)
                    self.assertEqual(len(contig), nmemb * itemsize)
                    initlst = [struct.unpack_from(fmt, contig, n*itemsize)
                               for n in range(nmemb)]
                    if len(initlst[0]) == 1:
                        initlst = [v[0] for v in initlst]

                    f = ND_FORTRAN if is_contiguous(result, 'F') else 0
                    y = ndarray(initlst, shape=shape, flags=f|ro, format=fmt)
                    self.assertEqual(memoryview(y), memoryview(result))

                    contig_bytes = memoryview(result).tobytes(order='A')
                    self.assertEqual(contig_bytes, contig)

        if is_memoryview_format(fmt):
            try:
                m = memoryview(result)
            except BufferError: # re-exporter does not provide full information
                return
            ex = result.obj if isinstance(result, memoryview) else result

            def check_memoryview(m, expected_readonly=readonly):
                self.assertIs(m.obj, ex)
                self.assertEqual(m.nbytes, expected_len)
                self.assertEqual(m.itemsize, itemsize)
                self.assertEqual(m.format, fmt)
                self.assertEqual(m.readonly, expected_readonly)
                self.assertEqual(m.ndim, ndim)
                self.assertEqual(m.shape, tuple(shape))
                if not (sliced and suboffsets):
                    self.assertEqual(m.strides, tuple(strides))
                self.assertEqual(m.suboffsets, tuple(suboffsets))

                if ndim == 0:
                    self.assertRaises(TypeError, len, m)
                else:
                    self.assertEqual(len(m), len(lst))

                rep = result.tolist() if fmt else result.tobytes()
                self.assertEqual(rep, lst)
                self.assertEqual(m, result)

            check_memoryview(m)
            with m.toreadonly() as mm:
                check_memoryview(mm, expected_readonly=True)
            m.tobytes()