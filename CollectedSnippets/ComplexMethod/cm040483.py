def _is_inf(x, pos=True):
    # NOTE: there is an ov_opset.is_inf but it does not catch
    # numpy infinite values like np.inf and -np.inf, hence why we have this
    # if this ever changes in OpenVINO, we can do this instead:
    # ov_opset.is_inf(x, {"detect_positive": pos, "detect_negative": not pos})
    # for each infinite sign
    inf_value = np.inf if pos else -np.inf
    x = get_ov_output(x)
    x_type = x.get_element_type()

    if x_type.is_integral() or x_type == Type.boolean:
        shape = ov_opset.shape_of(x, "i32").output(0)
        false_const = ov_opset.constant(False, Type.boolean).output(0)
        return OpenVINOKerasTensor(
            ov_opset.broadcast(false_const, shape).output(0)
        )

    if x_type == Type.bf16:
        x_f32 = ov_opset.convert(x, Type.f32).output(0)
        inf = ov_opset.constant(inf_value, Type.f32).output(0)
        is_inf = ov_opset.equal(x_f32, inf).output(0)
    else:
        if x_type == Type.f16:
            inf = ov_opset.constant(inf_value, Type.f16).output(0)
        elif x_type == Type.f32:
            inf = ov_opset.constant(inf_value, Type.f32).output(0)
        elif x_type == Type.f64:
            inf = ov_opset.constant(inf_value, Type.f64).output(0)
        else:
            inf = ov_opset.constant(inf_value, Type.f32).output(0)
        is_inf = ov_opset.equal(x, inf).output(0)
    return OpenVINOKerasTensor(is_inf)