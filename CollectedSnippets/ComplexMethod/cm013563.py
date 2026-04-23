def __eq__(self, other: object) -> bool:
        if isinstance(other, CalcMaxPool):
            return (
                self.maxpool_result == other.maxpool_result
                and self.input_var == other.input_var
                and self.kernel == other.kernel
                and self.padding == other.padding
                and self.stride == other.stride
                and self.dilation == other.dilation
                and self.matching_constraint == other.matching_constraint
            )
        else:
            return False