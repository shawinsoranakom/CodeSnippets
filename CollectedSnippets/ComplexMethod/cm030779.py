def test_memoryview_array(self):

        def cmptest(testcase, a, b, m, singleitem):
            for i, _ in enumerate(a):
                ai = a[i]
                mi = m[i]
                testcase.assertEqual(ai, mi)
                a[i] = singleitem
                if singleitem != ai:
                    testcase.assertNotEqual(a, m)
                    testcase.assertNotEqual(a, b)
                else:
                    testcase.assertEqual(a, m)
                    testcase.assertEqual(a, b)
                m[i] = singleitem
                testcase.assertEqual(a, m)
                testcase.assertEqual(b, m)
                a[i] = ai
                m[i] = mi

        for n in range(1, 5):
            for fmt, items, singleitem in iter_format(n, 'array'):
                for lslice in genslices(n):
                    for rslice in genslices(n):

                        a = array.array(fmt, items)
                        b = array.array(fmt, items)
                        m = memoryview(b)

                        self.assertEqual(m, a)
                        self.assertEqual(m.tolist(), a.tolist())
                        self.assertEqual(m.tobytes(), a.tobytes())
                        self.assertEqual(len(m), len(a))

                        cmptest(self, a, b, m, singleitem)

                        array_err = None
                        have_resize = None
                        try:
                            al = a[lslice]
                            ar = a[rslice]
                            a[lslice] = a[rslice]
                            have_resize = len(al) != len(ar)
                        except Exception as e:
                            array_err = e.__class__

                        m_err = None
                        try:
                            m[lslice] = m[rslice]
                        except Exception as e:
                            m_err = e.__class__

                        if have_resize: # memoryview cannot change shape
                            self.assertIs(m_err, ValueError)
                        elif m_err or array_err:
                            self.assertIs(m_err, array_err)
                        else:
                            self.assertEqual(m, a)
                            self.assertEqual(m.tolist(), a.tolist())
                            self.assertEqual(m.tobytes(), a.tobytes())
                            cmptest(self, a, b, m, singleitem)