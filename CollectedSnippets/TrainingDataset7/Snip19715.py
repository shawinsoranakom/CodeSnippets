def test_model_forms(self):
        fields = ["tenant", "id", "user_id", "text", "integer"]
        self.assertEqual(list(CommentForm.base_fields), fields)

        form = modelform_factory(Comment, fields="__all__")
        self.assertEqual(list(form().fields), fields)

        with self.assertRaisesMessage(
            FieldError, "Unknown field(s) (pk) specified for Comment"
        ):
            self.assertIsNone(modelform_factory(Comment, fields=["pk"]))