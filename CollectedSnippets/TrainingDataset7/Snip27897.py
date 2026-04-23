def test_class_getitem(self):
        self.assertIs(models.ForeignKey["Foo"], models.ForeignKey)