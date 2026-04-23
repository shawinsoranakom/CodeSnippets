def test_str_operations(self):
        try: 'a' + 5
        except TypeError: pass
        else: self.fail("'' + 5 doesn't raise TypeError")

        try: ''.split('')
        except ValueError: pass
        else: self.fail("''.split('') doesn't raise ValueError")

        try: ''.join([0])
        except TypeError: pass
        else: self.fail("''.join([0]) doesn't raise TypeError")

        try: ''.rindex('5')
        except ValueError: pass
        else: self.fail("''.rindex('5') doesn't raise ValueError")

        try: '%(n)s' % None
        except TypeError: pass
        else: self.fail("'%(n)s' % None doesn't raise TypeError")

        try: '%(n' % {}
        except ValueError: pass
        else: self.fail("'%(n' % {} '' doesn't raise ValueError")

        try: '%*s' % ('abc')
        except TypeError: pass
        else: self.fail("'%*s' % ('abc') doesn't raise TypeError")

        try: '%*.*s' % ('abc', 5)
        except TypeError: pass
        else: self.fail("'%*.*s' % ('abc', 5) doesn't raise TypeError")

        try: '%s' % (1, 2)
        except TypeError: pass
        else: self.fail("'%s' % (1, 2) doesn't raise TypeError")

        try: '%' % None
        except ValueError: pass
        else: self.fail("'%' % None doesn't raise ValueError")

        self.assertEqual('534253'.isdigit(), 1)
        self.assertEqual('534253x'.isdigit(), 0)
        self.assertEqual('%c' % 5, '\x05')
        self.assertEqual('%c' % '5', '5')