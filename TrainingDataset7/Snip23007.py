def test_absolute_max_invalid(self):
        msg = "'absolute_max' must be greater or equal to 'max_num'."
        for max_num in [None, 31]:
            with self.subTest(max_num=max_num):
                with self.assertRaisesMessage(ValueError, msg):
                    formset_factory(FavoriteDrinkForm, max_num=max_num, absolute_max=30)