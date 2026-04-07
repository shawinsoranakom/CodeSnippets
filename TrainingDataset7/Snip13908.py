def get_memo(self, testcase):
        try:
            memo = getattr(testcase, self.memo_attr)
        except AttributeError:
            memo = {}
            setattr(testcase, self.memo_attr, memo)
        return memo