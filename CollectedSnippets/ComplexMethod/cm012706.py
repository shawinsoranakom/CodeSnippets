def handle_scalar(scalar):
                if isinstance(scalar, int):
                    return f"PyLong_FromLongLong({scalar})"
                if isinstance(scalar, float):
                    return f"PyFloat_FromDouble({self.generate_float_value(scalar)})"
                if isinstance(scalar, bool):
                    return f"PyBool_FromLong({1 if scalar else 0})"
                if isinstance(scalar, complex):
                    real = self.generate_float_value(scalar.real)
                    imag = self.generate_float_value(scalar.imag)
                    return f"PyComplex_FromDoubles({real}, {imag})"
                if isinstance(scalar, SymTypes):
                    scalar_var = cexpr(scalar.node.expr)
                    if isinstance(scalar, torch.SymBool):
                        return f"PyBool_FromLong({scalar_var})"
                    if isinstance(scalar, torch.SymFloat):
                        return f"PyFloat_FromDouble({scalar_var})"
                    return f"PyLong_FromLongLong({scalar_var})"
                raise NotImplementedError(
                    f"scalar {scalar}, {type(scalar)} cannot be handled by handle_scalar"
                )