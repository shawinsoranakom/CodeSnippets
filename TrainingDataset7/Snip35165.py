def get_runner(self):
        return unittest.TextTestRunner(stream=StringIO())