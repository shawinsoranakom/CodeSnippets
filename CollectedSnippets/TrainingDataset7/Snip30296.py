def test_abstract_base_with_model_fields(self):
        msg = (
            "Abstract base class containing model fields not permitted for proxy model "
            "'NoAbstract'."
        )
        with self.assertRaisesMessage(TypeError, msg):

            class NoAbstract(Abstract):
                class Meta:
                    proxy = True