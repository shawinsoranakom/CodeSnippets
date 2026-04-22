def run_command(self, command):
        return subprocess.check_output(self.parameterize(command)).decode("UTF-8")