def test_uuid_unsupported(self):
        with self.assertRaises(TypeError):

            class Identifier(uuid.UUID, models.Choices):
                A = "972ce4eb-a95f-4a56-9339-68c208a76f18"