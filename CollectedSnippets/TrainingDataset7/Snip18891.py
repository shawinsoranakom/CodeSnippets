def test_cannot_create_instance_with_invalid_kwargs(self):
        msg = "Article() got unexpected keyword arguments: 'foo'"
        with self.assertRaisesMessage(TypeError, msg):
            Article(
                id=None,
                headline="Some headline",
                pub_date=datetime(2005, 7, 31),
                foo="bar",
            )
        msg = "Article() got unexpected keyword arguments: 'foo', 'bar'"
        with self.assertRaisesMessage(TypeError, msg):
            Article(
                id=None,
                headline="Some headline",
                pub_date=datetime(2005, 7, 31),
                foo="bar",
                bar="baz",
            )