def run(self):
                from random import randrange

                # Create all interesting powers of 2.
                values = []
                for exp in range(self.bitsize + 3):
                    values.append(1 << exp)

                # Add some random values.
                for i in range(self.bitsize):
                    val = 0
                    for j in range(self.bytesize):
                        val = (val << 8) | randrange(256)
                    values.append(val)

                # Values absorbed from other tests
                values.extend([300, 700000, sys.maxsize*4])

                # Try all those, and their negations, and +-1 from
                # them.  Note that this tests all power-of-2
                # boundaries in range, and a few out of range, plus
                # +-(2**n +- 1).
                for base in values:
                    for val in -base, base:
                        for incr in -1, 0, 1:
                            x = val + incr
                            self.test_one(x)

                # Some error cases.
                class NotAnInt:
                    def __int__(self):
                        return 42

                # Objects with an '__index__' method should be allowed
                # to pack as integers.  That is assuming the implemented
                # '__index__' method returns an 'int'.
                class Indexable(object):
                    def __init__(self, value):
                        self._value = value

                    def __index__(self):
                        return self._value

                # If the '__index__' method raises a type error, then
                # '__int__' should be used with a deprecation warning.
                class BadIndex(object):
                    def __index__(self):
                        raise TypeError

                    def __int__(self):
                        return 42

                self.assertRaises((TypeError, struct.error),
                                  struct.pack, self.format,
                                  "a string")
                self.assertRaises((TypeError, struct.error),
                                  struct.pack, self.format,
                                  randrange)
                self.assertRaises((TypeError, struct.error),
                                  struct.pack, self.format,
                                  3+42j)
                self.assertRaises((TypeError, struct.error),
                                  struct.pack, self.format,
                                  NotAnInt())
                self.assertRaises((TypeError, struct.error),
                                  struct.pack, self.format,
                                  BadIndex())

                # Check for legitimate values from '__index__'.
                for obj in (Indexable(0), Indexable(10), Indexable(17),
                            Indexable(42), Indexable(100), Indexable(127)):
                    try:
                        struct.pack(format, obj)
                    except:
                        self.fail("integer code pack failed on object "
                                  "with '__index__' method")

                # Check for bogus values from '__index__'.
                for obj in (Indexable(b'a'), Indexable('b'), Indexable(None),
                            Indexable({'a': 1}), Indexable([1, 2, 3])):
                    self.assertRaises((TypeError, struct.error),
                                      struct.pack, self.format,
                                      obj)