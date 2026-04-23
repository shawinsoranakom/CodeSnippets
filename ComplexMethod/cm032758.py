def check(self):
        self.check_valid_value(self.delimiter_mode, "Delimiter mode abnormal.", ["token_size", "delimiter", "one"])
        if self.delimiters is None:
            self.delimiters = []
        elif isinstance(self.delimiters, str):
            self.delimiters = [self.delimiters]
        else:
            self.delimiters = [d for d in self.delimiters if isinstance(d, str)]
        self.delimiters = [d for d in self.delimiters if d]

        if self.children_delimiters is None:
            self.children_delimiters = []
        elif isinstance(self.children_delimiters, str):
            self.children_delimiters = [self.children_delimiters]
        else:
            self.children_delimiters = [d for d in self.children_delimiters if isinstance(d, str)]
        self.children_delimiters = [d for d in self.children_delimiters if d]

        self.check_positive_integer(self.chunk_token_size, "Chunk token size.")
        self.check_decimal_float(self.overlapped_percent, "Overlapped percentage: [0, 1)")
        self.check_nonnegative_number(self.table_context_size, "Table context size.")
        self.check_nonnegative_number(self.image_context_size, "Image context size.")