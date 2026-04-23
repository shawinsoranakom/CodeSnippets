def test_name_ending_with_underscore(self):
        class Model_(models.Model):
            pass

        self.assertEqual(
            Model_.check(),
            [
                Error(
                    "The model name 'Model_' cannot start or end with an underscore "
                    "as it collides with the query lookup syntax.",
                    obj=Model_,
                    id="models.E023",
                )
            ],
        )