def test_f_expressions(self):
        self.assertIs(Author.objects.order_by(F("pk")).totally_ordered, True)
        self.assertIs(Author.objects.order_by(F("name")).totally_ordered, False)