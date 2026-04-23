def __init__(self, scope, body_file):
                super().__init__(scope, body_file)
                raise RequestDataTooBig()