def test_lazy_model_operation(self, apps):
        """
        Tests apps.lazy_model_operation().
        """
        model_classes = []
        initial_pending = set(apps._pending_operations)

        def test_func(*models):
            model_classes[:] = models

        class LazyA(models.Model):
            pass

        # Test models appearing twice, and models appearing consecutively
        model_keys = [
            ("apps", model_name)
            for model_name in ["lazya", "lazyb", "lazyb", "lazyc", "lazya"]
        ]
        apps.lazy_model_operation(test_func, *model_keys)

        # LazyModelA shouldn't be waited on since it's already registered,
        # and LazyModelC shouldn't be waited on until LazyModelB exists.
        self.assertEqual(
            set(apps._pending_operations) - initial_pending, {("apps", "lazyb")}
        )

        # Multiple operations can wait on the same model
        apps.lazy_model_operation(test_func, ("apps", "lazyb"))

        class LazyB(models.Model):
            pass

        self.assertEqual(model_classes, [LazyB])

        # Now we are just waiting on LazyModelC.
        self.assertEqual(
            set(apps._pending_operations) - initial_pending, {("apps", "lazyc")}
        )

        class LazyC(models.Model):
            pass

        # Everything should be loaded - make sure the callback was executed
        # properly.
        self.assertEqual(model_classes, [LazyA, LazyB, LazyB, LazyC, LazyA])