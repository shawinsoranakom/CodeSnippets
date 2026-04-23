def test_integerfield_subclass(self):
        """
        Class-defined widget is not overwritten by __init__() (#22245).
        """

        class MyIntegerField(IntegerField):
            widget = Textarea

        f = MyIntegerField()
        self.assertEqual(f.widget.__class__, Textarea)
        f = MyIntegerField(localize=True)
        self.assertEqual(f.widget.__class__, Textarea)