def test_invalid_loading_order(self):
        """
        Test for issue 10405
        """

        class A(models.Model):
            ref = models.ForeignKey("B", models.CASCADE)

        class Meta:
            model = A
            fields = "__all__"

        msg = (
            "Cannot create form field for 'ref' yet, because "
            "its related model 'B' has not been loaded yet"
        )
        with self.assertRaisesMessage(ValueError, msg):
            ModelFormMetaclass("Form", (ModelForm,), {"Meta": Meta})

        class B(models.Model):
            pass