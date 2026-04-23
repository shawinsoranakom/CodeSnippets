def test_invalid_sender_model_name(self):
        msg = (
            "Invalid model reference 'invalid'. String model references must be of the "
            "form 'app_label.ModelName'."
        )
        with self.assertRaisesMessage(ValueError, msg):
            signals.post_init.connect(self.receiver, sender="invalid")