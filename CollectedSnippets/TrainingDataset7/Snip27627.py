def assertRelated(self, model, needle):
        self.assertEqual(
            get_related_models_recursive(model),
            {(n._meta.app_label, n._meta.model_name) for n in needle},
        )