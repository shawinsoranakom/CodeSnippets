def test_get_next_prev_by_field_unsaved(self):
        msg = "get_next/get_previous cannot be used on unsaved objects."
        with self.assertRaisesMessage(ValueError, msg):
            Event().get_next_by_when()
        with self.assertRaisesMessage(ValueError, msg):
            Event().get_previous_by_when()