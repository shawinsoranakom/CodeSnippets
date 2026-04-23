def add_upsample_nearest2d(self, node):
        if not (node.inputsSize() == 3 or node.inputsSize() == 4):
            raise AssertionError(
                f"expected node.inputsSize() == 3 or 4, got {node.inputsSize()}"
            )
        if node.outputsSize() != 1:
            raise AssertionError(
                f"expected node.outputsSize() == 1, got {node.outputsSize()}"
            )
        if node.inputsSize() == 3:
            image, size_jit, scale_jit = node.inputs()
        else:
            image, size_jit, scale_h_jit, scale_w_jit = node.inputs()
        size_ctype, size_arg = self.get_constant_value(size_jit)

        if node.inputsSize() == 3:
            scale_ctype, scale_arg = self.get_constant_value(scale_jit)  # type: ignore[possibly-undefined]
        else:
            scale_h_ctype, scale_h_arg = self.get_constant_value(scale_h_jit)  # type: ignore[possibly-undefined]
            scale_w_ctype, _scale_w_arg = self.get_constant_value(scale_w_jit)  # type: ignore[possibly-undefined]

            # The only way for the 4-argument overload of upsample_nearest2d to
            # have been added to the graph without error is if the scale_h and
            # scale_w arguments are None
            if scale_h_ctype.kind() != "NoneType":
                raise AssertionError(
                    f"expected scale_h_ctype NoneType, got {scale_h_ctype.kind()}"
                )
            if scale_w_ctype.kind() != "NoneType":
                raise AssertionError(
                    f"expected scale_w_ctype NoneType, got {scale_w_ctype.kind()}"
                )

            scale_ctype = scale_h_ctype
            scale_arg = scale_h_arg

        image_id, image_oper = self.get_tensor_operand_by_jitval(image)
        if len(image_oper.shape) != 4:
            raise AssertionError(
                f"expected len(image_oper.shape) == 4, got {len(image_oper.shape)}"
            )

        if size_ctype.kind() != "NoneType" and scale_ctype.kind() != "NoneType":
            raise Exception("Size and scale cannot both be non-None.")  # noqa: TRY002
        elif size_ctype.kind() != "NoneType":
            if size_ctype.kind() != "ListType":
                raise AssertionError(
                    f"expected size_ctype ListType, got {size_ctype.kind()}"
                )
            if size_ctype.getElementType().kind() != "IntType":
                raise AssertionError(
                    f"expected size element type IntType, got {size_ctype.getElementType().kind()}"
                )
            if scale_ctype.kind() != "NoneType":
                raise AssertionError(
                    f"expected scale_ctype NoneType, got {scale_ctype.kind()}"
                )
            if scale_arg is not None:
                raise AssertionError(f"expected scale_arg None, got {scale_arg}")
            if not isinstance(size_arg, list):
                raise AssertionError(
                    f"expected size_arg to be list, got {type(size_arg)}"
                )
            if not size_arg:
                raise AssertionError("expected size_arg to be non-empty")
            if not all(isinstance(val, int) for val in size_arg):
                raise AssertionError("expected all size_arg values to be int")
            if len(size_arg) == 1:
                size_arg = size_arg * 2
            if len(size_arg) != 2:
                raise AssertionError(
                    f"expected len(size_arg) == 2, got {len(size_arg)}"
                )
            out_h = size_arg[0]
            out_w = size_arg[1]
            arg_h = self.add_immediate_int_scalar(out_h)
            arg_w = self.add_immediate_int_scalar(out_w)
        elif scale_ctype.kind() != "NoneType":
            if scale_ctype.kind() != "ListType":
                raise AssertionError(
                    f"expected scale_ctype ListType, got {scale_ctype.kind()}"
                )
            if scale_ctype.getElementType().kind() != "FloatType":
                raise AssertionError(
                    f"expected scale element type FloatType, got {scale_ctype.getElementType().kind()}"
                )
            if size_ctype.kind() != "NoneType":
                raise AssertionError(
                    f"expected size_ctype NoneType, got {size_ctype.kind()}"
                )
            if size_arg is not None:
                raise AssertionError(f"expected size_arg None, got {size_arg}")
            if not isinstance(scale_arg, list):
                raise AssertionError(
                    f"expected scale_arg to be list, got {type(scale_arg)}"
                )
            if not scale_arg:
                raise AssertionError("expected scale_arg to be non-empty")
            if not all(isinstance(val, float) for val in scale_arg):
                raise AssertionError("expected all scale_arg values to be float")
            if len(scale_arg) == 1:
                scale_arg = scale_arg * 2
            if len(scale_arg) != 2:
                raise AssertionError(
                    f"expected len(scale_arg) == 2, got {len(scale_arg)}"
                )
            out_h = int(scale_arg[0] * image_oper.shape[2])
            out_w = int(scale_arg[1] * image_oper.shape[3])
            arg_h = self.add_immediate_float_scalar(scale_arg[0])
            arg_w = self.add_immediate_float_scalar(scale_arg[1])
        else:
            raise Exception("Size and scale cannot both be None.")  # noqa: TRY002

        out_shape = (image_oper.shape[0], image_oper.shape[1], out_h, out_w)
        use_nchw = image_oper.use_nchw()
        out_id = self.add_tensor_operand(
            node.outputsAt(0), image_oper._replace(shape=out_shape)
        )

        if image_oper.shape[0] == 0 or image_oper.shape[1] == 0:
            raise Exception("Flexible batch or channels not supported")  # noqa: TRY002

        # Handle variable input size
        for dim in (2, 3):  # h, w indices
            if image_oper.shape[dim] == 0:
                if size_ctype.kind() != "NoneType":
                    # pyrefly: ignore [unsupported-operation]
                    self.compute_operand_shape(out_id, dim, size_arg[dim - 2])
                elif scale_ctype.kind() != "NoneType":
                    self.compute_operand_shape(
                        out_id,
                        dim,
                        # pyrefly: ignore [unsupported-operation]
                        f"int({scale_arg[dim - 2]} * {flex_name(image_id, dim)})",
                    )
                else:
                    raise Exception(  # noqa: TRY002
                        "Size and scale cannot both be None."
                    )

        inputs = [None] * 4
        inputs[0] = image_id
        inputs[1] = arg_w
        inputs[2] = arg_h
        inputs[3] = self.add_immediate_bool_scalar(use_nchw)

        outputs = [None] * 1
        outputs[0] = out_id

        self.add_operation(NNAPI_OperationCode.RESIZE_NEAREST_NEIGHBOR, inputs, outputs)