def _ask_default(self, default=""):
        """
        Prompt for a default value.

        The ``default`` argument allows providing a custom default value (as a
        string) which will be shown to the user and used as the return value
        if the user doesn't provide any other input.
        """
        self.prompt_output.write("Please enter the default value as valid Python.")
        if default:
            self.prompt_output.write(
                f"Accept the default '{default}' by pressing 'Enter' or "
                f"provide another value."
            )
        self.prompt_output.write(
            "The datetime and django.utils.timezone modules are available, so "
            "it is possible to provide e.g. timezone.now as a value."
        )
        self.prompt_output.write("Type 'exit' to exit this prompt")
        while True:
            if default:
                prompt = "[default: {}] >>> ".format(default)
            else:
                prompt = ">>> "
            self.prompt_output.write(prompt, ending="")
            try:
                code = input()
            except KeyboardInterrupt:
                self.prompt_output.write("\nCancelled.")
                sys.exit(1)
            if not code and default:
                code = default
            if not code:
                self.prompt_output.write(
                    "Please enter some code, or 'exit' (without quotes) to exit."
                )
            elif code == "exit":
                sys.exit(1)
            else:
                try:
                    return eval(code, {}, {"datetime": datetime, "timezone": timezone})
                except Exception as e:
                    self.prompt_output.write(f"{e.__class__.__name__}: {e}")