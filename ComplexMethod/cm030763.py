def verify_getbuf(self, orig_ex, ex, req, sliced=False):
        def match(req, flag):
            return ((req&flag) == flag)

        if (# writable request to read-only exporter
            (ex.readonly and match(req, PyBUF_WRITABLE)) or
            # cannot match explicit contiguity request
            (match(req, PyBUF_C_CONTIGUOUS) and not ex.c_contiguous) or
            (match(req, PyBUF_F_CONTIGUOUS) and not ex.f_contiguous) or
            (match(req, PyBUF_ANY_CONTIGUOUS) and not ex.contiguous) or
            # buffer needs suboffsets
            (not match(req, PyBUF_INDIRECT) and ex.suboffsets) or
            # buffer without strides must be C-contiguous
            (not match(req, PyBUF_STRIDES) and not ex.c_contiguous) or
            # PyBUF_SIMPLE|PyBUF_FORMAT and PyBUF_WRITABLE|PyBUF_FORMAT
            (not match(req, PyBUF_ND) and match(req, PyBUF_FORMAT))):

            self.assertRaises(BufferError, ndarray, ex, getbuf=req)
            return

        if isinstance(ex, ndarray) or is_memoryview_format(ex.format):
            lst = ex.tolist()
        else:
            nd = ndarray(ex, getbuf=PyBUF_FULL_RO)
            lst = nd.tolist()

        # The consumer may have requested default values or a NULL format.
        ro = False if match(req, PyBUF_WRITABLE) else ex.readonly
        fmt = ex.format
        itemsize = ex.itemsize
        ndim = ex.ndim
        if not match(req, PyBUF_FORMAT):
            # itemsize refers to the original itemsize before the cast.
            # The equality product(shape) * itemsize = len still holds.
            # The equality calcsize(format) = itemsize does _not_ hold.
            fmt = ''
            lst = orig_ex.tobytes() # Issue 12834
        if not match(req, PyBUF_ND):
            ndim = 1
        shape = orig_ex.shape if match(req, PyBUF_ND) else ()
        strides = orig_ex.strides if match(req, PyBUF_STRIDES) else ()

        nd = ndarray(ex, getbuf=req)
        self.verify(nd, obj=ex,
                    itemsize=itemsize, fmt=fmt, readonly=ro,
                    ndim=ndim, shape=shape, strides=strides,
                    lst=lst, sliced=sliced)