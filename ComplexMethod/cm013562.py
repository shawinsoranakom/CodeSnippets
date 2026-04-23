def __eq__(self, other: object) -> bool:
        if isinstance(other, CalcConv):
            return (
                self.conv_result == other.conv_result
                and self.input_var == other.input_var
                and self.c_out == other.c_out
                and self.kernel == other.kernel
                and self.padding == other.padding
                and self.stride == other.stride
                and self.dilation == other.dilation
                and self.matching_constraint == other.matching_constraint
            )
        else:
            return False