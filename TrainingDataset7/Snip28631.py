def test_repr(self):
        index = models.Index(fields=["title"])
        named_index = models.Index(fields=["title"], name="title_idx")
        multi_col_index = models.Index(fields=["title", "author"])
        partial_index = models.Index(
            fields=["title"], name="long_books_idx", condition=models.Q(pages__gt=400)
        )
        covering_index = models.Index(
            fields=["title"],
            name="include_idx",
            include=["author", "pages"],
        )
        opclasses_index = models.Index(
            fields=["headline", "body"],
            name="opclasses_idx",
            opclasses=["varchar_pattern_ops", "text_pattern_ops"],
        )
        func_index = models.Index(Lower("title"), "subtitle", name="book_func_idx")
        tablespace_index = models.Index(
            fields=["title"],
            db_tablespace="idx_tbls",
            name="book_tablespace_idx",
        )
        self.assertEqual(repr(index), "<Index: fields=['title']>")
        self.assertEqual(
            repr(named_index),
            "<Index: fields=['title'] name='title_idx'>",
        )
        self.assertEqual(repr(multi_col_index), "<Index: fields=['title', 'author']>")
        self.assertEqual(
            repr(partial_index),
            "<Index: fields=['title'] name='long_books_idx' "
            "condition=(AND: ('pages__gt', 400))>",
        )
        self.assertEqual(
            repr(covering_index),
            "<Index: fields=['title'] name='include_idx' "
            "include=('author', 'pages')>",
        )
        self.assertEqual(
            repr(opclasses_index),
            "<Index: fields=['headline', 'body'] name='opclasses_idx' "
            "opclasses=['varchar_pattern_ops', 'text_pattern_ops']>",
        )
        self.assertEqual(
            repr(func_index),
            "<Index: expressions=(Lower(F(title)), F(subtitle)) "
            "name='book_func_idx'>",
        )
        self.assertEqual(
            repr(tablespace_index),
            "<Index: fields=['title'] name='book_tablespace_idx' "
            "db_tablespace='idx_tbls'>",
        )