def test_objecttypes(self):
        # check all types defined in Objects/
        calcsize = struct.calcsize
        size = test.support.calcobjsize
        vsize = test.support.calcvobjsize
        check = self.check_sizeof
        # bool
        check(True, vsize('') + self.longdigit)
        check(False, vsize('') + self.longdigit)
        # buffer
        # XXX
        # builtin_function_or_method
        check(len, size('5P'))
        # bytearray
        samples = [b'', b'u'*100000]
        for sample in samples:
            x = bytearray(sample)
            check(x, vsize('n2PiP') + x.__alloc__())
        # bytearray_iterator
        check(iter(bytearray()), size('nP'))
        # bytes
        check(b'', vsize('n') + 1)
        check(b'x' * 10, vsize('n') + 11)
        # cell
        def get_cell():
            x = 42
            def inner():
                return x
            return inner
        check(get_cell().__closure__[0], size('P'))
        # code
        def check_code_size(a, expected_size):
            self.assertGreaterEqual(sys.getsizeof(a), expected_size)
        check_code_size(get_cell().__code__, size('6i13P'))
        check_code_size(get_cell.__code__, size('6i13P'))
        def get_cell2(x):
            def inner():
                return x
            return inner
        check_code_size(get_cell2.__code__, size('6i13P') + calcsize('n'))
        # complex
        check(complex(0,1), size('2d'))
        # method_descriptor (descriptor object)
        check(str.lower, size('3PPP'))
        # classmethod_descriptor (descriptor object)
        # XXX
        # member_descriptor (descriptor object)
        import datetime
        check(datetime.timedelta.days, size('3PP'))
        # getset_descriptor (descriptor object)
        import collections
        check(collections.defaultdict.default_factory, size('3PP'))
        # wrapper_descriptor (descriptor object)
        check(int.__add__, size('3P2P'))
        # method-wrapper (descriptor object)
        check({}.__iter__, size('2P'))
        # empty dict
        check({}, size('nQ2P'))
        # dict (string key)
        check({"a": 1}, size('nQ2P') + calcsize(DICT_KEY_STRUCT_FORMAT) + 8 + (8*2//3)*calcsize('2P'))
        longdict = {str(i): i for i in range(8)}
        check(longdict, size('nQ2P') + calcsize(DICT_KEY_STRUCT_FORMAT) + 16 + (16*2//3)*calcsize('2P'))
        # dict (non-string key)
        check({1: 1}, size('nQ2P') + calcsize(DICT_KEY_STRUCT_FORMAT) + 8 + (8*2//3)*calcsize('n2P'))
        longdict = {1:1, 2:2, 3:3, 4:4, 5:5, 6:6, 7:7, 8:8}
        check(longdict, size('nQ2P') + calcsize(DICT_KEY_STRUCT_FORMAT) + 16 + (16*2//3)*calcsize('n2P'))
        # dictionary-keyview
        check({}.keys(), size('P'))
        # dictionary-valueview
        check({}.values(), size('P'))
        # dictionary-itemview
        check({}.items(), size('P'))
        # dictionary iterator
        check(iter({}), size('P2nPn'))
        # dictionary-keyiterator
        check(iter({}.keys()), size('P2nPn'))
        # dictionary-valueiterator
        check(iter({}.values()), size('P2nPn'))
        # dictionary-itemiterator
        check(iter({}.items()), size('P2nPn'))
        # dictproxy
        class C(object): pass
        check(C.__dict__, size('P'))
        # BaseException
        check(BaseException(), size('6Pb'))
        # UnicodeEncodeError
        check(UnicodeEncodeError("", "", 0, 0, ""), size('6Pb 2P2nP'))
        # UnicodeDecodeError
        check(UnicodeDecodeError("", b"", 0, 0, ""), size('6Pb 2P2nP'))
        # UnicodeTranslateError
        check(UnicodeTranslateError("", 0, 1, ""), size('6Pb 2P2nP'))
        # ellipses
        check(Ellipsis, size(''))
        # EncodingMap
        import codecs, encodings.iso8859_3
        x = codecs.charmap_build(encodings.iso8859_3.decoding_table)
        check(x, size('32B2iB'))
        # enumerate
        check(enumerate([]), size('n4P'))
        # reverse
        check(reversed(''), size('nP'))
        # float
        check(float(0), size('d'))
        # sys.floatinfo
        check(sys.float_info, self.P + vsize('') + self.P * len(sys.float_info))
        # frame
        def func():
            return sys._getframe()
        x = func()
        if support.Py_GIL_DISABLED:
            INTERPRETER_FRAME = '9PihcP'
        else:
            INTERPRETER_FRAME = '9PhcP'
        check(x, size('3PiccPPP' + INTERPRETER_FRAME + 'P'))
        # function
        def func(): pass
        check(func, size('16Pi'))
        class c():
            @staticmethod
            def foo():
                pass
            @classmethod
            def bar(cls):
                pass
            # staticmethod
            check(foo, size('PP'))
            # classmethod
            check(bar, size('PP'))
        # generator
        def get_gen(): yield 1
        check(get_gen(), size('6P4c' + INTERPRETER_FRAME + 'P'))
        # iterator
        check(iter('abc'), size('lP'))
        # callable-iterator
        import re
        check(re.finditer('',''), size('2P'))
        # list
        check(list([]), vsize('Pn'))
        check(list([1]), vsize('Pn') + 2*self.P)
        check(list([1, 2]), vsize('Pn') + 2*self.P)
        check(list([1, 2, 3]), vsize('Pn') + 4*self.P)
        # sortwrapper (list)
        # XXX
        # cmpwrapper (list)
        # XXX
        # listiterator (list)
        check(iter([]), size('lP'))
        # listreverseiterator (list)
        check(reversed([]), size('nP'))
        # int
        check(0, vsize('') + self.longdigit)
        check(1, vsize('') + self.longdigit)
        check(-1, vsize('') + self.longdigit)
        PyLong_BASE = 2**sys.int_info.bits_per_digit
        check(int(PyLong_BASE), vsize('') + 2*self.longdigit)
        check(int(PyLong_BASE**2-1), vsize('') + 2*self.longdigit)
        check(int(PyLong_BASE**2), vsize('') + 3*self.longdigit)
        # module
        if support.Py_GIL_DISABLED:
            md_gil = '?'
        else:
            md_gil = ''
        check(unittest, size('PPPP?' + md_gil + 'NPPPPP'))
        # None
        check(None, size(''))
        # NotImplementedType
        check(NotImplemented, size(''))
        # object
        check(object(), size(''))
        # property (descriptor object)
        class C(object):
            def getx(self): return self.__x
            def setx(self, value): self.__x = value
            def delx(self): del self.__x
            x = property(getx, setx, delx, "")
            check(x, size('5Pi'))
        # PyCapsule
        try:
            import _datetime
        except ModuleNotFoundError:
            pass
        else:
            check(_datetime.datetime_CAPI, size('6P'))
        # rangeiterator
        check(iter(range(1)), size('3l'))
        check(iter(range(2**65)), size('3P'))
        # reverse
        check(reversed(''), size('nP'))
        # range
        check(range(1), size('4P'))
        check(range(66000), size('4P'))
        # set
        # frozenset
        PySet_MINSIZE = 8
        samples = [[], range(10), range(50)]
        s = size('3nP' + PySet_MINSIZE*'nP' + '2nP')
        for sample in samples:
            minused = len(sample)
            if minused == 0: tmp = 1
            # the computation of minused is actually a bit more complicated
            # but this suffices for the sizeof test
            minused = minused*2
            newsize = PySet_MINSIZE
            while newsize <= minused:
                newsize = newsize << 1
            if newsize <= 8:
                check(set(sample), s)
                check(frozenset(sample), s)
            else:
                check(set(sample), s + newsize*calcsize('nP'))
                check(frozenset(sample), s + newsize*calcsize('nP'))
        # setiterator
        check(iter(set()), size('P3n'))
        # slice
        check(slice(0), size('3P'))
        # super
        check(super(int), size('3P'))
        # tuple
        check((), vsize('') + self.P)
        check((1,2,3), vsize('') + self.P + 3*self.P)
        # type
        # static type: PyTypeObject
        fmt = 'P2nPI13Pl4Pn9Pn12PI2Pc'
        s = vsize(fmt)
        check(int, s)
        typeid = 'n' if support.Py_GIL_DISABLED else ''
        # class
        s = vsize(fmt +                 # PyTypeObject
                  '4P'                  # PyAsyncMethods
                  '36P'                 # PyNumberMethods
                  '3P'                  # PyMappingMethods
                  '10P'                 # PySequenceMethods
                  '2P'                  # PyBufferProcs
                  '7P'
                  '1PIP'                # Specializer cache
                  + typeid              # heap type id (free-threaded only)
                  )
        class newstyleclass(object): pass
        # Separate block for PyDictKeysObject with 8 keys and 5 entries
        check(newstyleclass, s + calcsize(DICT_KEY_STRUCT_FORMAT) + 64 + 42*calcsize("2P"))
        # dict with shared keys
        [newstyleclass() for _ in range(100)]
        check(newstyleclass().__dict__, size('nQ2P') + self.P)
        o = newstyleclass()
        o.a = o.b = o.c = o.d = o.e = o.f = o.g = o.h = 1
        # Separate block for PyDictKeysObject with 16 keys and 10 entries
        check(newstyleclass, s + calcsize(DICT_KEY_STRUCT_FORMAT) + 64 + 42*calcsize("2P"))
        # dict with shared keys
        check(newstyleclass().__dict__, size('nQ2P') + self.P)
        # unicode
        # each tuple contains a string and its expected character size
        # don't put any static strings here, as they may contain
        # wchar_t or UTF-8 representations
        samples = ['1'*100, '\xff'*50,
                   '\u0100'*40, '\uffff'*100,
                   '\U00010000'*30, '\U0010ffff'*100]
        # also update field definitions in test_unicode.test_raiseMemError
        asciifields = "nnb"
        compactfields = asciifields + "nP"
        unicodefields = compactfields + "P"
        for s in samples:
            maxchar = ord(max(s))
            if maxchar < 128:
                L = size(asciifields) + len(s) + 1
            elif maxchar < 256:
                L = size(compactfields) + len(s) + 1
            elif maxchar < 65536:
                L = size(compactfields) + 2*(len(s) + 1)
            else:
                L = size(compactfields) + 4*(len(s) + 1)
            check(s, L)
        # verify that the UTF-8 size is accounted for
        s = chr(0x4000)   # 4 bytes canonical representation
        check(s, size(compactfields) + 4)
        # compile() will trigger the generation of the UTF-8
        # representation as a side effect
        compile(s, "<stdin>", "eval")
        check(s, size(compactfields) + 4 + 4)
        # TODO: add check that forces the presence of wchar_t representation
        # TODO: add check that forces layout of unicodefields
        # weakref
        import weakref
        if support.Py_GIL_DISABLED:
            expected = size('2Pn4P')
        else:
            expected = size('2Pn3P')
        check(weakref.ref(int), expected)
        # weakproxy
        # XXX
        # weakcallableproxy
        check(weakref.proxy(int), expected)