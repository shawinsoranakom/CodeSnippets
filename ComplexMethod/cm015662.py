def forward(self, x):
        global _variable, _variable_2

        if self.mode == 1:
            if torch.compiler.is_compiling():
                _variable += 1
            else:
                _variable_2 += 1
        elif self.mode == 2:
            if user_function():
                _variable += 1
        elif self.mode == 3:
            lambda_f = lambda: torch.compiler.is_compiling()  # noqa: E731
            if lambda_f():
                _variable += 1
        elif self.mode == 4:
            for cond in user_generator():
                if cond:
                    _variable += 1
        elif self.mode == 5:
            x += 1
        elif self.mode == 6:
            if user_function():
                torch._dynamo.graph_break()
                _variable += 1
        return x