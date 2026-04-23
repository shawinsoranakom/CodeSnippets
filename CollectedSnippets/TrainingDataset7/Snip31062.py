def handle_raw_input(
        self, input_data, META, content_length, boundary, encoding=None
    ):
        return ("_POST", "_FILES")