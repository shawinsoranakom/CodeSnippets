def _check_correct_val(val):
        if val is None:
            return True
        elif isinstance(val, (int, bool, str, float)):
            return True
        elif isinstance(
            val, (torch.memory_format, torch.dtype, torch.device, torch.layout)
        ):
            return True
        elif isinstance(
            val, (FakeTensor, torch.Tensor)
        ):  # TODO(zhxchen17) Remove Tensor.
            return True
        elif isinstance(val, (SymInt, SymFloat, SymBool)):
            return True
        elif isinstance(val, CustomObjArgument):
            return True
        elif isinstance(val, Iterable):
            return all(_check_correct_val(x) for x in val)
        elif is_opaque_type(type(val)):
            return True
        return False