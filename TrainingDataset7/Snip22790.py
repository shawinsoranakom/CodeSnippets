def test_validators_independence(self):
        """
        The list of form field validators can be modified without polluting
        other forms.
        """

        class MyForm(Form):
            myfield = CharField(max_length=25)

        f1 = MyForm()
        f2 = MyForm()

        f1.fields["myfield"].validators[0] = MaxValueValidator(12)
        self.assertNotEqual(
            f1.fields["myfield"].validators[0], f2.fields["myfield"].validators[0]
        )