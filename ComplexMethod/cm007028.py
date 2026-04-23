def process_data(self) -> Data | list[Data]:
        if isinstance(self.data_input, list):
            true_output = []
            false_output = []
            for item in self.data_input:
                if self.validate_input(item):
                    result = self.process_single_data(item)
                    if result:
                        true_output.append(item)
                    else:
                        false_output.append(item)
            self.stop("false_output" if true_output else "true_output")
            return true_output or false_output
        if not self.validate_input(self.data_input):
            return Data(data={"error": self.status})
        result = self.process_single_data(self.data_input)
        self.stop("false_output" if result else "true_output")
        return self.data_input