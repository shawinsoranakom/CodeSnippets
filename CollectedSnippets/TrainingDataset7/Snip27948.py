def test_post_init_not_connected(self):
        person_model_id = id(self.PersonModel)
        self.assertNotIn(
            person_model_id,
            [sender_id for (_, sender_id), *_ in signals.post_init.receivers],
        )