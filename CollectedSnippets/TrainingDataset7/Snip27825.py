def test_save_without_float_conversion(self):
        """
        Ensure decimals don't go through a corrupting float conversion during
        save (#5079).
        """
        bd = BigD(d="12.9")
        bd.save()
        bd = BigD.objects.get(pk=bd.pk)
        self.assertEqual(bd.d, Decimal("12.9"))