def assert_kernelized_forward_is_the_same(self, model_1, model_2):
        """
        Iterate over modules and check if the forward method is the same between
        the kernelized and not kernelized models. Break on first difference, else continue.
        Finally, assert that at least one forward is the same.
        """
        no_difference = True
        for (name1, module1), (name2, module2) in zip(model_1.named_modules(), model_2.named_modules()):
            # Only compare modules with the same name
            if name1 != name2:
                continue
            # Check if both modules have a 'forward' attribute
            if hasattr(module1, "forward") and hasattr(module2, "forward"):
                # Compare the code objects of the forward methods
                code1 = getattr(module1.forward, "__code__", None)
                code2 = getattr(module2.forward, "__code__", None)
                if code1 is not None and code2 is not None:
                    if code1 != code2:
                        no_difference = False
                        break
        self.assertTrue(
            no_difference,
            "All module's forward methods were the same between the two models",
        )