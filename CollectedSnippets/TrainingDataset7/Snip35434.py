def setUp(self):
                calls.append("setUp")
                self.addCleanup(lambda: calls.append("cleanup"))