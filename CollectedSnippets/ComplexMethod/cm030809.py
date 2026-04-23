def test_unsafe_object_compare(self):

        # This test is by ppperry. It ensures that unsafe_object_compare is
        # verifying ms->key_richcompare == tp->richcompare before comparing.

        class WackyComparator(int):
            def __lt__(self, other):
                elem.__class__ = WackyList2
                return int.__lt__(self, other)

        class WackyList1(list):
            pass

        class WackyList2(list):
            def __lt__(self, other):
                raise ValueError

        L = [WackyList1([WackyComparator(i), i]) for i in range(10)]
        elem = L[-1]
        with self.assertRaises(ValueError):
            L.sort()

        L = [WackyList1([WackyComparator(i), i]) for i in range(10)]
        elem = L[-1]
        with self.assertRaises(ValueError):
            [(x,) for x in L].sort()

        # The following test is also by ppperry. It ensures that
        # unsafe_object_compare handles Py_NotImplemented appropriately.
        class PointlessComparator:
            def __lt__(self, other):
                return NotImplemented
        L = [PointlessComparator(), PointlessComparator()]
        self.assertRaises(TypeError, L.sort)
        self.assertRaises(TypeError, [(x,) for x in L].sort)

        # The following tests go through various types that would trigger
        # ms->key_compare = unsafe_object_compare
        lists = [list(range(100)) + [(1<<70)],
                 [str(x) for x in range(100)] + ['\uffff'],
                 [bytes(x) for x in range(100)],
                 [cmp_to_key(lambda x,y: x<y)(x) for x in range(100)]]
        for L in lists:
            check_against_PyObject_RichCompareBool(self, L)