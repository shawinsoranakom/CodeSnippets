def assert_kernelized_forward_is_different(self, kernelized_model, not_kernelized_model):
        """
        Iterate over modules and check if the forward method is different between
        the kernelized and not kernelized models. Break on first difference, else continue.
        Finally, assert that at least one forward is different.
        """
        found_difference = False
        for (name1, module1), (name2, module2) in zip(
            kernelized_model.named_modules(), not_kernelized_model.named_modules()
        ):
            # Only compare modules with the same name
            if name1 != name2:
                continue
            # Check if both modules have a 'forward' attribute
            if hasattr(module1, "forward") and hasattr(module2, "forward"):
                # Compare the code objects of the forward methods
                code1 = getattr(module1.forward, "__code__", None)
                code2 = getattr(module2.forward, "__code__", None)
                if code1 is not None and code2 is not None:
                    if code1 is not code2:
                        found_difference = True
                        break
        self.assertTrue(
            found_difference,
            "No module's forward method was different between kernelized and not kernelized models.",
        )