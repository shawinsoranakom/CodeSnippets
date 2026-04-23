def test_buffer_sizes(self):

        t1 = self.writeTmp(''.join("Line %s of file 1\n" % (i+1) for i in range(15)))
        t2 = self.writeTmp(''.join("Line %s of file 2\n" % (i+1) for i in range(10)))
        t3 = self.writeTmp(''.join("Line %s of file 3\n" % (i+1) for i in range(5)))
        t4 = self.writeTmp(''.join("Line %s of file 4\n" % (i+1) for i in range(1)))

        pat = re.compile(r'LINE (\d+) OF FILE (\d+)')

        if verbose:
            print('1. Simple iteration')
        fi = FileInput(files=(t1, t2, t3, t4), encoding="utf-8")
        lines = list(fi)
        fi.close()
        self.assertEqual(len(lines), 31)
        self.assertEqual(lines[4], 'Line 5 of file 1\n')
        self.assertEqual(lines[30], 'Line 1 of file 4\n')
        self.assertEqual(fi.lineno(), 31)
        self.assertEqual(fi.filename(), t4)

        if verbose:
            print('2. Status variables')
        fi = FileInput(files=(t1, t2, t3, t4), encoding="utf-8")
        s = "x"
        while s and s != 'Line 6 of file 2\n':
            s = fi.readline()
        self.assertEqual(fi.filename(), t2)
        self.assertEqual(fi.lineno(), 21)
        self.assertEqual(fi.filelineno(), 6)
        self.assertFalse(fi.isfirstline())
        self.assertFalse(fi.isstdin())

        if verbose:
            print('3. Nextfile')
        fi.nextfile()
        self.assertEqual(fi.readline(), 'Line 1 of file 3\n')
        self.assertEqual(fi.lineno(), 22)
        fi.close()

        if verbose:
            print('4. Stdin')
        fi = FileInput(files=(t1, t2, t3, t4, '-'), encoding="utf-8")
        savestdin = sys.stdin
        try:
            sys.stdin = StringIO("Line 1 of stdin\nLine 2 of stdin\n")
            lines = list(fi)
            self.assertEqual(len(lines), 33)
            self.assertEqual(lines[32], 'Line 2 of stdin\n')
            self.assertEqual(fi.filename(), '<stdin>')
            fi.nextfile()
        finally:
            sys.stdin = savestdin

        if verbose:
            print('5. Boundary conditions')
        fi = FileInput(files=(t1, t2, t3, t4), encoding="utf-8")
        self.assertEqual(fi.lineno(), 0)
        self.assertEqual(fi.filename(), None)
        fi.nextfile()
        self.assertEqual(fi.lineno(), 0)
        self.assertEqual(fi.filename(), None)

        if verbose:
            print('6. Inplace')
        savestdout = sys.stdout
        try:
            fi = FileInput(files=(t1, t2, t3, t4), inplace=True, encoding="utf-8")
            for line in fi:
                line = line[:-1].upper()
                print(line)
            fi.close()
        finally:
            sys.stdout = savestdout

        fi = FileInput(files=(t1, t2, t3, t4), encoding="utf-8")
        for line in fi:
            self.assertEqual(line[-1], '\n')
            m = pat.match(line[:-1])
            self.assertNotEqual(m, None)
            self.assertEqual(int(m.group(1)), fi.filelineno())
        fi.close()