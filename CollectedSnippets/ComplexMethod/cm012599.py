def _filter_pdl(self, code: IndentedBuffer):
        new_lines = []
        has_wait = False
        previous_launch = None
        for l in code._lines:
            if type(l) is str and self.GDC_WAIT in l:
                if has_wait:
                    continue
                else:
                    has_wait = True
            if type(l) is str and self.GDC_LAUNCH in l:
                if previous_launch is not None:
                    new_lines.pop(previous_launch)
                previous_launch = len(new_lines)
            new_lines.append(l)
        code._lines = new_lines