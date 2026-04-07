def _boolean_input(self, question, default=None):
        self.prompt_output.write(f"{question} ", ending="")
        result = input()
        if not result and default is not None:
            return default
        while not result or result[0].lower() not in "yn":
            self.prompt_output.write("Please answer yes or no: ", ending="")
            result = input()
        return result[0].lower() == "y"