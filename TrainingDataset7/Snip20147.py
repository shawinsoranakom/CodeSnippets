def test_bilateral_inner_qs(self):
        with register_lookup(models.CharField, UpperBilateralTransform):
            msg = "Bilateral transformations on nested querysets are not implemented."
            with self.assertRaisesMessage(NotImplementedError, msg):
                Author.objects.filter(
                    name__upper__in=Author.objects.values_list("name")
                )