def find_job(self, name, job=None):
        # attempt to find job by 'Ansible:' header comment
        comment = None
        for l in self.lines:
            if comment is not None:
                if comment == name:
                    return [comment, l]
                else:
                    comment = None
            elif re.match(r'%s' % self.ansible, l):
                comment = re.sub(r'%s' % self.ansible, '', l)

        # failing that, attempt to find job by exact match
        if job:
            for i, l in enumerate(self.lines):
                if l == job:
                    # if no leading ansible header, insert one
                    if not re.match(r'%s' % self.ansible, self.lines[i - 1]):
                        self.lines.insert(i, self.do_comment(name))
                        return [self.lines[i], l, True]
                    # if a leading blank ansible header AND job has a name, update header
                    elif name and self.lines[i - 1] == self.do_comment(None):
                        self.lines[i - 1] = self.do_comment(name)
                        return [self.lines[i - 1], l, True]

        return []