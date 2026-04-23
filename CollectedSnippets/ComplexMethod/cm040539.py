def _assert_input_compatibility(self, inputs):
        try:
            tree.assert_same_structure(inputs, self._inputs_struct)
        except ValueError:
            raise ValueError(
                "Function was called with an invalid input structure. "
                f"Expected input structure: {self._inputs_struct}\n"
                f"Received input structure: {inputs}"
            )
        for x, x_ref in zip(tree.flatten(inputs), self._inputs):
            if len(x.shape) != len(x_ref.shape):
                raise ValueError(
                    f"{self.__class__.__name__} was passed "
                    f"incompatible inputs. For input '{x_ref.name}', "
                    f"expected shape {x_ref.shape}, but received "
                    f"instead a tensor with shape {x.shape}."
                )
            for dim, ref_dim in zip(x.shape, x_ref.shape):
                if ref_dim is not None and dim is not None:
                    if dim != ref_dim:
                        raise ValueError(
                            f"{self.__class__.__name__} was passed "
                            f"incompatible inputs. For input '{x_ref.name}', "
                            f"expected shape {x_ref.shape}, but received "
                            f"instead a tensor with shape {x.shape}."
                        )