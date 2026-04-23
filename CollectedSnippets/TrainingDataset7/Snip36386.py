def test_linebreaks(self):
        items = (
            ("para1\n\npara2\r\rpara3", "<p>para1</p>\n\n<p>para2</p>\n\n<p>para3</p>"),
            (
                "para1\nsub1\rsub2\n\npara2",
                "<p>para1<br>sub1<br>sub2</p>\n\n<p>para2</p>",
            ),
            (
                "para1\r\n\r\npara2\rsub1\r\rpara4",
                "<p>para1</p>\n\n<p>para2<br>sub1</p>\n\n<p>para4</p>",
            ),
            ("para1\tmore\n\npara2", "<p>para1\tmore</p>\n\n<p>para2</p>"),
        )
        for value, output in items:
            with self.subTest(value=value, output=output):
                self.check_output(linebreaks, value, output)
                self.check_output(linebreaks, lazystr(value), output)