def view(x, dtype=None):
    """Reinterpret the bytes of a tensor as a different dtype.

    Three execution paths:
      1. **NumPy fast path** — plain ``np.ndarray`` inputs are viewed
         directly and re-wrapped as an OpenVINO constant.
      2. **Constant folding** — if the OpenVINO subgraph backing *x*
         is parameter-free (e.g. a ``Constant`` node *or* an expression
         such as ``Broadcast``), it is compiled on CPU and the resulting
         NumPy array is viewed.
      3. **Symbolic bitwise decomposition** — for non-constant,
         integer-to-integer type changes the bit pattern is preserved
         using shift / mask / OR operations in the OpenVINO graph.
         Float ↔ int reinterpretation on symbolic tensors is not
         supported because OpenVINO lacks a bitcast op.
    """
    from keras.src import backend

    new_dtype = backend.standardize_dtype(dtype) if dtype else None

    # Fast path: plain numpy/scalar inputs
    if isinstance(x, np.ndarray):
        if new_dtype is None:
            return OpenVINOKerasTensor(ov_opset.constant(x).output(0))
        return OpenVINOKerasTensor(
            ov_opset.constant(x.view(np.dtype(new_dtype))).output(0)
        )

    x_ov = get_ov_output(x)
    old_ov_type = x_ov.get_element_type()
    old_dtype = ov_to_keras_type(old_ov_type)

    if new_dtype is None:
        new_dtype = old_dtype
    new_ov_type = OPENVINO_DTYPES[new_dtype]

    if old_ov_type == new_ov_type:
        return OpenVINOKerasTensor(x_ov)

    old_itemsize = old_ov_type.size
    new_itemsize = new_ov_type.size

    # Constant folding: evaluate parameter-free subgraphs on CPU.
    # Uses raw bytes + ov.Tensor to avoid numpy dtype issues
    # (e.g. bfloat16 is not a standard numpy dtype).
    try:
        node = x_ov.get_node()
        if node.get_type_name() == "Constant":
            np_data = node.data
        else:
            ov_model = ov.Model(results=[x_ov], parameters=[])
            compiled = ov.compile_model(ov_model, "CPU")
            np_data = compiled({})[0]
        old_shape = np_data.shape
        new_last = old_shape[-1] * old_itemsize // new_itemsize
        new_shape = list(old_shape[:-1]) + [new_last]
        raw = np.frombuffer(np_data.tobytes(), dtype=np.uint8)
        result_tensor = ov.Tensor(new_ov_type, new_shape)
        np.copyto(
            np.frombuffer(result_tensor.data, dtype=np.uint8),
            raw,
        )
        return OpenVINOKerasTensor(ov_opset.constant(result_tensor).output(0))
    except Exception:
        pass

    # Non-constant tensors: only integer↔integer is supported
    if not (old_ov_type.is_integral() and new_ov_type.is_integral()):
        raise NotImplementedError(
            f"`view` from {old_dtype} to {new_dtype} is not supported "
            "for non-constant tensors with the OpenVINO backend "
            "(no bitcast operation available in OpenVINO opset)."
        )

    if old_itemsize == new_itemsize:
        # Same-width signed↔unsigned: convert preserves bit pattern
        return OpenVINOKerasTensor(
            ov_opset.convert(x_ov, new_ov_type).output(0)
        )
    elif old_itemsize > new_itemsize:
        return _view_int_expand(x_ov, new_ov_type, old_itemsize, new_itemsize)
    else:
        return _view_int_contract(x_ov, new_ov_type, old_itemsize, new_itemsize)