def test_custom_transform_annotation(self):
        with register_lookup(DecimalField, Floor):
            books = Book.objects.annotate(floor_price=F("price__floor"))

        self.assertCountEqual(
            books.values_list("pk", "floor_price"),
            [
                (self.b1.pk, 30),
                (self.b2.pk, 23),
                (self.b3.pk, 29),
                (self.b4.pk, 29),
                (self.b5.pk, 82),
                (self.b6.pk, 75),
            ],
        )