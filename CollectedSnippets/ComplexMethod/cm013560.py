def transform_var(
        tensor: TVar | TensorType | _DynType,
        counter: int,
        dimension_dict: dict[int, int],
    ) -> tuple[_Z3Expr, int]:
        """
        Transforms tensor variables to a format understood by z3
        Args:
            tensor: Tensor variable or a tensor type potentially with variable dimensions
        Returns: Transformed variable to a z3 format

        """
        if isinstance(tensor, TensorType):
            res: list[_Z3Expr] = []
            for t in tensor.__args__:
                transformed, counter = transform_dimension(t, counter, dimension_dict)
                res.append(transformed)

            if len(res) > 4:
                raise AssertionError(f"Expected res length <= 4, got {len(res)}")
            if len(tensor.__args__) == 1:
                return tensor_type.tensor1(res[0]), counter
            elif len(tensor.__args__) == 2:
                return tensor_type.tensor2(res[0], res[1]), counter
            elif len(tensor.__args__) == 3:
                return tensor_type.tensor3(res[0], res[1], res[2]), counter
            elif len(tensor.__args__) == 4:
                return tensor_type.tensor4(res[0], res[1], res[2], res[3]), counter
            else:
                raise AssertionError(
                    f"Unexpected tensor args length: {len(tensor.__args__)}"
                )

        elif tensor == Dyn:
            return z3_dyn, counter

        elif isinstance(tensor, TVar):
            return z3.Const(tensor.tvar, tensor_type), counter

        else:
            raise NotImplementedError(f"Unsupported tensor type: {type(tensor)}")