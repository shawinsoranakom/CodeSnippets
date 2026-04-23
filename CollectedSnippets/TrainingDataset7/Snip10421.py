def _choice_input(self, question, choices):
        self.prompt_output.write(f"{question}")
        for i, choice in enumerate(choices):
            self.prompt_output.write(" %s) %s" % (i + 1, choice))
        self.prompt_output.write("Select an option: ", ending="")
        while True:
            try:
                result = input()
                value = int(result)
            except ValueError:
                pass
            except KeyboardInterrupt:
                self.prompt_output.write("\nCancelled.")
                sys.exit(1)
            else:
                if 0 < value <= len(choices):
                    return value
            self.prompt_output.write("Please select a valid option: ", ending="")