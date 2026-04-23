def create_frame(self, module, input, output):
        self.expand_frame(f"{self.prefix} {self.module_names[module]} {module.__class__.__name__}")

        # params
        for name, p in module.named_parameters(recurse=False):
            self.analyse_variable(p, name)

        # inputs
        if isinstance(input, tuple):
            for i, x in enumerate(input):
                self.analyse_variable(x, f"input[{i}]")
        else:
            self.analyse_variable(input, "input")

        # outputs
        if isinstance(output, tuple):
            for i, x in enumerate(output):
                # possibly a tuple of tuples
                if isinstance(x, tuple):
                    for j, y in enumerate(x):
                        self.analyse_variable(y, f"output[{i}][{j}]")
                else:
                    self.analyse_variable(x, f"output[{i}]")
        else:
            self.analyse_variable(output, "output")

        self.save_frame()