def eval_line(self, s):
        if s.find(' -> ') >= 0 and s[:2] != '--' and not s.startswith('  --'):
            s = (s.split('->')[0] + '->' +
                 s.split('->')[1].split('--')[0]).strip()
        else:
            s = s.split('--')[0].strip()

        for ignore in self.ignore_list:
            if s.find(ignore) >= 0:
                #print s.split()[0], 'NotImplemented--', ignore
                return
        if not s:
            return
        elif ':' in s:
            return self.eval_directive(s)
        else:
            return self.eval_equation(s)