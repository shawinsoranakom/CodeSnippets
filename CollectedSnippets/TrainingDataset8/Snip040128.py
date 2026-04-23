def test_is_namedtuple(self):
        Boy = namedtuple("Boy", ("name", "age"))
        John = Boy("John", "29")

        res = type_util.is_namedtuple(John)
        self.assertTrue(res)