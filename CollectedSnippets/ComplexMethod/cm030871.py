def test_truth_values(self):
        if None: self.fail('None is true instead of false')
        if 0: self.fail('0 is true instead of false')
        if 0.0: self.fail('0.0 is true instead of false')
        if '': self.fail('\'\' is true instead of false')
        if not 1: self.fail('1 is false instead of true')
        if not 1.0: self.fail('1.0 is false instead of true')
        if not 'x': self.fail('\'x\' is false instead of true')
        if not {'x': 1}: self.fail('{\'x\': 1} is false instead of true')
        def f(): pass
        class C: pass
        x = C()
        if not f: self.fail('f is false instead of true')
        if not C: self.fail('C is false instead of true')
        if not sys: self.fail('sys is false instead of true')
        if not x: self.fail('x is false instead of true')