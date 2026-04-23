def test_lazy_reference_checks(self, apps):
        class DummyModel(models.Model):
            author = models.ForeignKey("Author", models.CASCADE)

            class Meta:
                app_label = "invalid_models_tests"

        class DummyClass:
            def __call__(self, **kwargs):
                pass

            def dummy_method(self):
                pass

        def dummy_function(*args, **kwargs):
            pass

        apps.lazy_model_operation(dummy_function, ("auth", "imaginarymodel"))
        apps.lazy_model_operation(dummy_function, ("fanciful_app", "imaginarymodel"))

        post_init.connect(dummy_function, sender="missing-app.Model", apps=apps)
        post_init.connect(DummyClass(), sender="missing-app.Model", apps=apps)
        post_init.connect(
            DummyClass().dummy_method, sender="missing-app.Model", apps=apps
        )

        self.assertEqual(
            _check_lazy_references(apps),
            [
                Error(
                    "%r contains a lazy reference to auth.imaginarymodel, "
                    "but app 'auth' doesn't provide model 'imaginarymodel'."
                    % dummy_function,
                    obj=dummy_function,
                    id="models.E022",
                ),
                Error(
                    "%r contains a lazy reference to fanciful_app.imaginarymodel, "
                    "but app 'fanciful_app' isn't installed." % dummy_function,
                    obj=dummy_function,
                    id="models.E022",
                ),
                Error(
                    "An instance of class 'DummyClass' was connected to "
                    "the 'post_init' signal with a lazy reference to the sender "
                    "'missing-app.model', but app 'missing-app' isn't installed.",
                    hint=None,
                    obj="invalid_models_tests.test_models",
                    id="signals.E001",
                ),
                Error(
                    "Bound method 'DummyClass.dummy_method' was connected to the "
                    "'post_init' signal with a lazy reference to the sender "
                    "'missing-app.model', but app 'missing-app' isn't installed.",
                    hint=None,
                    obj="invalid_models_tests.test_models",
                    id="signals.E001",
                ),
                Error(
                    "The field invalid_models_tests.DummyModel.author was declared "
                    "with a lazy reference to 'invalid_models_tests.author', but app "
                    "'invalid_models_tests' isn't installed.",
                    hint=None,
                    obj=DummyModel.author.field,
                    id="fields.E307",
                ),
                Error(
                    "The function 'dummy_function' was connected to the 'post_init' "
                    "signal with a lazy reference to the sender "
                    "'missing-app.model', but app 'missing-app' isn't installed.",
                    hint=None,
                    obj="invalid_models_tests.test_models",
                    id="signals.E001",
                ),
            ],
        )