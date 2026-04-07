def _tag_re_split_positions(self):
        last = 0
        for match in tag_re.finditer(self.template_string):
            start, end = match.span()
            yield last, start
            yield start, end
            last = end
        yield last, len(self.template_string)