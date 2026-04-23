def get_finders():
            class Finder1(BaseFinder):
                def check(self, **kwargs):
                    return [error1]

            class Finder2(BaseFinder):
                def check(self, **kwargs):
                    return []

            class Finder3(BaseFinder):
                def check(self, **kwargs):
                    return [error2, error3]

            class Finder4(BaseFinder):
                pass

            return [Finder1(), Finder2(), Finder3(), Finder4()]