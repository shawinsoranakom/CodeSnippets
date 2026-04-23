def go(expr: str, keypath: pytree.KeyPath):
                if keypath == ():
                    return expr

                if (
                    len(keypath) >= 2
                    and isinstance(keypath[0], CallMethodKey)
                    and isinstance(keypath[1], pytree.SequenceKey)
                ):
                    return go(
                        f"{expr}.{keypath[0].name}({keypath[1].idx})", keypath[2:]
                    )
                elif isinstance(keypath[0], CallMethodKey):
                    return go(f"{expr}.{keypath[0].name}()", keypath[1:])
                elif isinstance(keypath[0], pytree.SequenceKey):
                    return (
                        go(f"std::get<{keypath[0].idx}>({expr})", keypath[1:])
                        if V.graph.cpp_wrapper
                        else go(f"{expr}[{keypath[0].idx}]", keypath[1:])
                    )
                elif isinstance(keypath[0], DivideByKey):
                    # TODO: need to assert divisibility
                    # TODO: this is invalid C++ codegen
                    return go(f"{expr}.__floordiv__({keypath[0].divisor})", keypath[1:])
                else:
                    raise AssertionError(f"unrecognized keypath {keypath}")