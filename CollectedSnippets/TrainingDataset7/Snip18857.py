def test_no_error_when_filtering_with_expression(self):
        self.assertSequenceEqual(Square.objects.filter(id=Value(0, BigAutoField())), ())