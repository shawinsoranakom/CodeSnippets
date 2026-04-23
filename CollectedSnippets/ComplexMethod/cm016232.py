def fuzz_inputs_specs(self, output_spec: Spec) -> list[Spec]:
        """Generate input specs for general matrix multiplication."""
        if not isinstance(output_spec, TensorSpec):
            raise ValueError("MatmulOperator can only produce TensorSpec outputs")

        output_size = output_spec.size
        output_dims = len(output_size)

        dtypes = self._get_compatible_dtype(output_spec.dtype)

        if output_dims == 1:
            # Matrix-vector multiplication: (n,) = (k,) @ (k, n) or (n,) = (n, k) @ (k,)
            n = output_size[0]
            k = random.randint(1, 16)

            # Randomly choose between two valid patterns
            if random.choice([True, False]):
                # Pattern 1: (n,) = (k,) @ (k, n)
                input1_spec = TensorSpec(size=(k,), stride=(1,), dtype=dtypes[0])
                input2_spec = TensorSpec(
                    size=(k, n),
                    stride=(n, 1),
                    dtype=dtypes[1] if len(dtypes) > 1 else dtypes[0],
                )
            else:
                # Pattern 2: (n,) = (n, k) @ (k,)
                input1_spec = TensorSpec(size=(n, k), stride=(k, 1), dtype=dtypes[0])
                input2_spec = TensorSpec(
                    size=(k,),
                    stride=(1,),
                    dtype=dtypes[1] if len(dtypes) > 1 else dtypes[0],
                )

        elif output_dims == 2:
            # Matrix multiplication: (m, n) = (m, k) @ (k, n)
            m, n = output_size
            k = random.randint(1, 16)

            input1_spec = TensorSpec(size=(m, k), stride=(k, 1), dtype=dtypes[0])
            input2_spec = TensorSpec(
                size=(k, n),
                stride=(n, 1),
                dtype=dtypes[1] if len(dtypes) > 1 else dtypes[0],
            )

        else:
            # Batched matrix multiplication: (..., m, n) = (..., m, k) @ (..., k, n)
            *batch_dims, m, n = output_size
            k = random.randint(1, 16)

            # Calculate strides for contiguous tensors
            input1_size = tuple(batch_dims + [m, k])
            input2_size = tuple(batch_dims + [k, n])

            # Contiguous strides
            input1_stride = [1]
            for i in reversed(range(len(input1_size) - 1)):
                input1_stride.append(input1_stride[-1] * input1_size[i + 1])
            input1_stride = tuple(reversed(input1_stride))

            input2_stride = [1]
            for i in reversed(range(len(input2_size) - 1)):
                input2_stride.append(input2_stride[-1] * input2_size[i + 1])
            input2_stride = tuple(reversed(input2_stride))

            input1_spec = TensorSpec(
                size=input1_size, stride=input1_stride, dtype=dtypes[0]
            )
            input2_spec = TensorSpec(
                size=input2_size,
                stride=input2_stride,
                dtype=dtypes[1] if len(dtypes) > 1 else dtypes[0],
            )

        return [input1_spec, input2_spec]