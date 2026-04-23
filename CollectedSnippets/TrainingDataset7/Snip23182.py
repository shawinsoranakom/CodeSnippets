def test_valid_loading_order(self):
        """
        Test for issue 10405
        """

        class C(models.Model):
            ref = models.ForeignKey("D", models.CASCADE)

        class D(models.Model):
            pass

        class Meta:
            model = C
            fields = "__all__"

        self.assertTrue(
            issubclass(
                ModelFormMetaclass("Form", (ModelForm,), {"Meta": Meta}), ModelForm
            )
        )