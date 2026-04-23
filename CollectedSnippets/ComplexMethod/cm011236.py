def dtype_mismatch(self, other: "Op") -> bool:
        if (
            (
                self.type not in ["scatter", "gather", "broadcast"]
                and set(self.input_dtypes) != set(self.output_dtypes)
                and self.input_sizes[0]
                and self.output_sizes[0]
            )
            or (
                self.type not in ["scatter", "broadcast"]
                and set(self.input_dtypes) != set(other.input_dtypes)
                and self.input_sizes[0]
                and other.input_sizes[0]
            )
            or (
                self.type != "gather"
                and set(self.output_dtypes) != set(other.output_dtypes)
                and self.output_sizes[0]
                and other.output_sizes[0]
            )
        ):
            return True
        return False