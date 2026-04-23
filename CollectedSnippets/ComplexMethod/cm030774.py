def test_py_buffer_to_contiguous(self):

        # The requests are used in _testbuffer.c:py_buffer_to_contiguous
        # to generate buffers without full information for testing.
        requests = (
            # distinct flags
            PyBUF_INDIRECT, PyBUF_STRIDES, PyBUF_ND, PyBUF_SIMPLE,
            # compound requests
            PyBUF_FULL, PyBUF_FULL_RO,
            PyBUF_RECORDS, PyBUF_RECORDS_RO,
            PyBUF_STRIDED, PyBUF_STRIDED_RO,
            PyBUF_CONTIG, PyBUF_CONTIG_RO,
        )

        # no buffer interface
        self.assertRaises(TypeError, py_buffer_to_contiguous, {}, 'F',
                          PyBUF_FULL_RO)

        # scalar, read-only request
        nd = ndarray(9, shape=(), format="L", flags=ND_WRITABLE)
        for order in ['C', 'F', 'A']:
            for request in requests:
                b = py_buffer_to_contiguous(nd, order, request)
                self.assertEqual(b, nd.tobytes())

        # zeros in shape
        nd = ndarray([1], shape=[0], format="L", flags=ND_WRITABLE)
        for order in ['C', 'F', 'A']:
            for request in requests:
                b = py_buffer_to_contiguous(nd, order, request)
                self.assertEqual(b, b'')

        nd = ndarray(list(range(8)), shape=[2, 0, 7], format="L",
                     flags=ND_WRITABLE)
        for order in ['C', 'F', 'A']:
            for request in requests:
                b = py_buffer_to_contiguous(nd, order, request)
                self.assertEqual(b, b'')

        ### One-dimensional arrays are trivial, since Fortran and C order
        ### are the same.

        # one-dimensional
        for f in [0, ND_FORTRAN]:
            nd = ndarray([1], shape=[1], format="h", flags=f|ND_WRITABLE)
            ndbytes = nd.tobytes()
            for order in ['C', 'F', 'A']:
                for request in requests:
                    b = py_buffer_to_contiguous(nd, order, request)
                    self.assertEqual(b, ndbytes)

            nd = ndarray([1, 2, 3], shape=[3], format="b", flags=f|ND_WRITABLE)
            ndbytes = nd.tobytes()
            for order in ['C', 'F', 'A']:
                for request in requests:
                    b = py_buffer_to_contiguous(nd, order, request)
                    self.assertEqual(b, ndbytes)

        # one-dimensional, non-contiguous input
        nd = ndarray([1, 2, 3], shape=[2], strides=[2], flags=ND_WRITABLE)
        ndbytes = nd.tobytes()
        for order in ['C', 'F', 'A']:
            for request in [PyBUF_STRIDES, PyBUF_FULL]:
                b = py_buffer_to_contiguous(nd, order, request)
                self.assertEqual(b, ndbytes)

        nd = nd[::-1]
        ndbytes = nd.tobytes()
        for order in ['C', 'F', 'A']:
            for request in requests:
                try:
                    b = py_buffer_to_contiguous(nd, order, request)
                except BufferError:
                    continue
                self.assertEqual(b, ndbytes)

        ###
        ### Multi-dimensional arrays:
        ###
        ### The goal here is to preserve the logical representation of the
        ### input array but change the physical representation if necessary.
        ###
        ### _testbuffer example:
        ### ====================
        ###
        ###    C input array:
        ###    --------------
        ###       >>> nd = ndarray(list(range(12)), shape=[3, 4])
        ###       >>> nd.tolist()
        ###       [[0, 1, 2, 3],
        ###        [4, 5, 6, 7],
        ###        [8, 9, 10, 11]]
        ###
        ###    Fortran output:
        ###    ---------------
        ###       >>> py_buffer_to_contiguous(nd, 'F', PyBUF_FULL_RO)
        ###       >>> b'\x00\x04\x08\x01\x05\t\x02\x06\n\x03\x07\x0b'
        ###
        ###    The return value corresponds to this input list for
        ###    _testbuffer's ndarray:
        ###       >>> nd = ndarray([0,4,8,1,5,9,2,6,10,3,7,11], shape=[3,4],
        ###                        flags=ND_FORTRAN)
        ###       >>> nd.tolist()
        ###       [[0, 1, 2, 3],
        ###        [4, 5, 6, 7],
        ###        [8, 9, 10, 11]]
        ###
        ###    The logical array is the same, but the values in memory are now
        ###    in Fortran order.
        ###
        ### NumPy example:
        ### ==============
        ###    _testbuffer's ndarray takes lists to initialize the memory.
        ###    Here's the same sequence in NumPy:
        ###
        ###    C input:
        ###    --------
        ###       >>> nd = ndarray(buffer=bytearray(list(range(12))),
        ###                        shape=[3, 4], dtype='B')
        ###       >>> nd
        ###       array([[ 0,  1,  2,  3],
        ###              [ 4,  5,  6,  7],
        ###              [ 8,  9, 10, 11]], dtype=uint8)
        ###
        ###    Fortran output:
        ###    ---------------
        ###       >>> fortran_buf = nd.tobytes(order='F')
        ###       >>> fortran_buf
        ###       b'\x00\x04\x08\x01\x05\t\x02\x06\n\x03\x07\x0b'
        ###
        ###       >>> nd = ndarray(buffer=fortran_buf, shape=[3, 4],
        ###                        dtype='B', order='F')
        ###
        ###       >>> nd
        ###       array([[ 0,  1,  2,  3],
        ###              [ 4,  5,  6,  7],
        ###              [ 8,  9, 10, 11]], dtype=uint8)
        ###

        # multi-dimensional, contiguous input
        lst = list(range(12))
        for f in [0, ND_FORTRAN]:
            nd = ndarray(lst, shape=[3, 4], flags=f|ND_WRITABLE)
            if numpy_array:
                na = numpy_array(buffer=bytearray(lst),
                                 shape=[3, 4], dtype='B',
                                 order='C' if f == 0 else 'F')

            # 'C' request
            if f == ND_FORTRAN: # 'F' to 'C'
                x = ndarray(transpose(lst, [4, 3]), shape=[3, 4],
                            flags=ND_WRITABLE)
                expected = x.tobytes()
            else:
                expected = nd.tobytes()
            for request in requests:
                try:
                    b = py_buffer_to_contiguous(nd, 'C', request)
                except BufferError:
                    continue

                self.assertEqual(b, expected)

                # Check that output can be used as the basis for constructing
                # a C array that is logically identical to the input array.
                y = ndarray([v for v in b], shape=[3, 4], flags=ND_WRITABLE)
                self.assertEqual(memoryview(y), memoryview(nd))

                if numpy_array:
                    self.assertEqual(b, na.tobytes(order='C'))

            # 'F' request
            if f == 0: # 'C' to 'F'
                x = ndarray(transpose(lst, [3, 4]), shape=[4, 3],
                            flags=ND_WRITABLE)
            else:
                x = ndarray(lst, shape=[3, 4], flags=ND_WRITABLE)
            expected = x.tobytes()
            for request in [PyBUF_FULL, PyBUF_FULL_RO, PyBUF_INDIRECT,
                            PyBUF_STRIDES, PyBUF_ND]:
                try:
                    b = py_buffer_to_contiguous(nd, 'F', request)
                except BufferError:
                    continue
                self.assertEqual(b, expected)

                # Check that output can be used as the basis for constructing
                # a Fortran array that is logically identical to the input array.
                y = ndarray([v for v in b], shape=[3, 4], flags=ND_FORTRAN|ND_WRITABLE)
                self.assertEqual(memoryview(y), memoryview(nd))

                if numpy_array:
                    self.assertEqual(b, na.tobytes(order='F'))

            # 'A' request
            if f == ND_FORTRAN:
                x = ndarray(lst, shape=[3, 4], flags=ND_WRITABLE)
                expected = x.tobytes()
            else:
                expected = nd.tobytes()
            for request in [PyBUF_FULL, PyBUF_FULL_RO, PyBUF_INDIRECT,
                            PyBUF_STRIDES, PyBUF_ND]:
                try:
                    b = py_buffer_to_contiguous(nd, 'A', request)
                except BufferError:
                    continue

                self.assertEqual(b, expected)

                # Check that output can be used as the basis for constructing
                # an array with order=f that is logically identical to the input
                # array.
                y = ndarray([v for v in b], shape=[3, 4], flags=f|ND_WRITABLE)
                self.assertEqual(memoryview(y), memoryview(nd))

                if numpy_array:
                    self.assertEqual(b, na.tobytes(order='A'))

        # multi-dimensional, non-contiguous input
        nd = ndarray(list(range(12)), shape=[3, 4], flags=ND_WRITABLE|ND_PIL)

        # 'C'
        b = py_buffer_to_contiguous(nd, 'C', PyBUF_FULL_RO)
        self.assertEqual(b, nd.tobytes())
        y = ndarray([v for v in b], shape=[3, 4], flags=ND_WRITABLE)
        self.assertEqual(memoryview(y), memoryview(nd))

        # 'F'
        b = py_buffer_to_contiguous(nd, 'F', PyBUF_FULL_RO)
        x = ndarray(transpose(lst, [3, 4]), shape=[4, 3], flags=ND_WRITABLE)
        self.assertEqual(b, x.tobytes())
        y = ndarray([v for v in b], shape=[3, 4], flags=ND_FORTRAN|ND_WRITABLE)
        self.assertEqual(memoryview(y), memoryview(nd))

        # 'A'
        b = py_buffer_to_contiguous(nd, 'A', PyBUF_FULL_RO)
        self.assertEqual(b, nd.tobytes())
        y = ndarray([v for v in b], shape=[3, 4], flags=ND_WRITABLE)
        self.assertEqual(memoryview(y), memoryview(nd))