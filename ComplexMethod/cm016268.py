def is_arg_smaller(t1: Type, t2: Type) -> bool:
        return (
            str(t1) == "Scalar"
            and str(t2) == "Tensor"
            or str(t1) == "Scalar?"
            and str(t2) == "Tensor?"
            or "Dimname" in str(t1)
            and "Dimname" not in str(t2)
            or
            # In the discussion https://github.com/pytorch/pytorch/issues/54555 it has been
            # discussed why it is important to prioritize int/int? over int[]
            str(t1) == "int[]"
            and (str(t2) == "int" or str(t2) == "int?")
            or
            # TensorList currently throws an error during argument parsing, that's why it needs to be
            # last in signature ordering. See discussion: https://github.com/pytorch/pytorch/issues/58087
            str(t1) == "Tensor[]"
            and str(t2).find("[]") != -1
            or
            # Prioritize IntArrayRef overload over SymIntArrayRef
            str(t1) == "SymInt[]"
            and str(t2) == "int[]"
            or
            # Make sure both in, SymInt are sorted consistently w.r.t. Tensor since Tensor can be implicitly
            # converted to either int or SymInt.  Prioritize the Tensor overload since it otherwise gets shadowed.
            (str(t1) == "SymInt" or str(t1) == "int")
            and str(t2) == "Tensor"
        )