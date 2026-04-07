def __init__(self, test, shutil_which_result="nonexistent"):
        self.stdout = StringIO()
        self.stderr = StringIO()
        self.test = test
        self.shutil_which_result = shutil_which_result