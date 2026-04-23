def test_empty_querydict_args(self):
        data = QueryDict()
        files = QueryDict()
        p = Person(data, files)
        self.assertIs(p.data, data)
        self.assertIs(p.files, files)