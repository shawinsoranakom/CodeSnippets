def test_nullable_relation(self):
        im = Image.objects.create(name="imag1")
        p1 = Product.objects.create(name="Django Plushie", image=im)
        p2 = Product.objects.create(name="Talking Django Plushie")

        with self.assertNumQueries(1):
            result = sorted(
                Product.objects.select_related("image"), key=lambda x: x.name
            )
            self.assertEqual(
                [p.name for p in result], ["Django Plushie", "Talking Django Plushie"]
            )

            self.assertEqual(p1.image, im)
            # Check for ticket #13839
            self.assertIsNone(p2.image)