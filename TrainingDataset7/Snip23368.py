def test_selectdate_required(self):
        class GetNotRequiredDate(Form):
            mydate = DateField(widget=SelectDateWidget, required=False)

        class GetRequiredDate(Form):
            mydate = DateField(widget=SelectDateWidget, required=True)

        self.assertFalse(GetNotRequiredDate().fields["mydate"].widget.is_required)
        self.assertTrue(GetRequiredDate().fields["mydate"].widget.is_required)