def test_register_and_run_checks(self):
        def f(**kwargs):
            calls[0] += 1
            return [1, 2, 3]

        def f2(**kwargs):
            return [4]

        def f3(**kwargs):
            return [5]

        calls = [0]

        # test register as decorator
        registry = CheckRegistry()
        registry.register()(f)
        registry.register("tag1", "tag2")(f2)
        registry.register("tag2", deploy=True)(f3)

        # test register as function
        registry2 = CheckRegistry()
        registry2.register(f)
        registry2.register(f2, "tag1", "tag2")
        registry2.register(f3, "tag2", deploy=True)

        # check results
        errors = registry.run_checks()
        errors2 = registry2.run_checks()
        self.assertEqual(errors, errors2)
        self.assertEqual(sorted(errors), [1, 2, 3, 4])
        self.assertEqual(calls[0], 2)

        errors = registry.run_checks(tags=["tag1"])
        errors2 = registry2.run_checks(tags=["tag1"])
        self.assertEqual(errors, errors2)
        self.assertEqual(sorted(errors), [4])

        errors = registry.run_checks(
            tags=["tag1", "tag2"], include_deployment_checks=True
        )
        errors2 = registry2.run_checks(
            tags=["tag1", "tag2"], include_deployment_checks=True
        )
        self.assertEqual(errors, errors2)
        self.assertEqual(sorted(errors), [4, 5])