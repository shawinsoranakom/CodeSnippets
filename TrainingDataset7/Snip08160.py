def is_in_comment(self, pos, comments):
        for start, end in comments:
            if start < pos and pos < end:
                return True
            if pos < start:
                return False
        return False