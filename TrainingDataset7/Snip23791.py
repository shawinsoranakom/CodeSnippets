def test_late_form_validation(self):
        """
        A form can be marked invalid in the form_valid() method (#25548).
        """
        res = self.client.post("/late-validation/", {"name": "Me", "message": "Hello"})
        self.assertFalse(res.context["form"].is_valid())