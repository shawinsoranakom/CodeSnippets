def report(self, verbose=False, width=None):
        # Prepare format
        if not width:
            width = min(self.max_width, shutil.get_terminal_size()[0] - 24)
        hr = "-" * (width + 24) + "\n"
        fmt = '{k:%d}{lines:>8}{other:>8}{code:>8}\n' % (width,)

        # Render
        s = fmt.format(k="Odoo cloc", lines="Line", other="Other", code="Code")
        s += hr
        for m in sorted(self.modules):
            s += fmt.format(k=m, lines=self.total[m], other=self.total[m]-self.code[m], code=self.code[m])
            if verbose:
                for i in sorted(self.modules[m], key=lambda i: self.modules[m][i][0], reverse=True):
                    code, total = self.modules[m][i]
                    s += fmt.format(k='    ' + i, lines=total, other=total - code, code=code)
        s += hr
        total = sum(self.total.values())
        code = sum(self.code.values())
        s += fmt.format(k='', lines=total, other=total - code, code=code)
        print(s)

        if self.excluded and verbose:
            ex = fmt.format(k="Excluded", lines="Line", other="Other", code="Code")
            ex += hr
            for m in sorted(self.excluded):
                for i in sorted(self.excluded[m], key=lambda i: self.excluded[m][i][0], reverse=True):
                    code, total = self.excluded[m][i]
                    ex += fmt.format(k='    ' + i, lines=total, other=total - code, code=code)
            ex += hr
            print(ex)

        if self.errors:
            e = "\nErrors\n\n"
            for m in sorted(self.errors):
                e += "{}\n".format(m)
                for i in sorted(self.errors[m]):
                    e += fmt.format(k='    ' + i, lines=self.errors[m][i], other='', code='')
            print(e)