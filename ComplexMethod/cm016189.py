def unroll(num_unrolls, IndexType, InType, OutType):
    def compute_output(num_unrolls, InType, is_main):
        code = []

        pred = "svAll" if is_main else "pg"
        if InType == "float":
            for i in range(num_unrolls):
                code.append(f"        output = svmla_x({pred}, output, svld1(svAll, &ip{i}[k]), wgt{i});")
        elif InType == "at::Half":
            for i in range(num_unrolls):
                code.append(f"        auto input{i} = svcvt_f32_x({pred}, svreinterpret_f16(\n"
                f"          svld1uh_u32({pred}, reinterpret_cast<const uint16_t*>(&ip{i}[k]))));")
            for i in range(num_unrolls):
                code.append(f"        output = svmla_x({pred}, output, input{i}, wgt{i});")
        elif InType == "at::BFloat16":
            for i in range(num_unrolls):
                code.append(f"        auto input{i} = svreinterpret_f32(svlsl_x({pred},\n"
                f"          svld1uh_u32({pred}, reinterpret_cast<const uint16_t*>(&ip{i}[k])), 16));")
            for i in range(num_unrolls):
                code.append(f"        output = svmla_x({pred}, output, input{i}, wgt{i});")
        elif InType == "uint8_t":
            code.append(f"        output = svadd_x({pred}, output, bio);")
            for i in range(num_unrolls):
                code.append(f"        auto input{i} = svcvt_f32_x({pred}, svld1ub_u32({pred}, &ip{i}[k]));")
            for i in range(num_unrolls):
                code.append(f"        output = svmla_x({pred}, output, input{i}, wgt{i});")
        else:
            raise ValueError(f'Unknown datatype "{InType}"')

        return code

    code = []

    if num_unrolls == 1:
        code.append("    // tail loop")
        code.append("    if (j < end_offset) {")
    else:
        code.append(f"    // unrolling {num_unrolls} times")
        code.append(f"    while (j + {num_unrolls - 1} < end_offset) {{")
    for i in range(num_unrolls):
        code.append(f"      const auto idx{i} = indices[pos + {i}];")

    # check indices
    for i in range(num_unrolls):
        code.append(
            f"      if (idx{i} < 0 || idx{i} >= data_size) {{\n"
            + "        return false;\n"
            + "      }"
        )

    if InType == "uint8_t":
        for i in range(num_unrolls):
            code.append(f"      {OutType} wgt{i} = 1.f;")
        code.append(f"      {OutType} bio = 0.f;")
    else:
        for i in range(num_unrolls):
            code.append(f"      {OutType} wgt{i} = 1.f;")

    code.append("      if (weights) {")
    for i in range(num_unrolls):
        code.append(f"        wgt{i} = weights[IS_WEIGHT_POSITIONAL ? (j + {i} - start_offset) : pos + {i}];")
    code.append("      }")
    if InType == "uint8_t":
        code.append("      if (scale_bias) {")
        for i in range(num_unrolls):
            code.append(f"        bio += wgt{i} * scale_bias[2 * idx{i} + 1];")
            code.append(f"        wgt{i} = wgt{i} * scale_bias[2 * idx{i}];")
        code.append("      }")

    for i in range(num_unrolls):
        code.append(f"      const {InType}* const ip{i} = &input[idx{i} * block_size];")

    # compute and store
    code.append("      svbool_t pg;")
    code.append("      int64_t k = 0;")
    # main loop
    code.append("      while (k + vLen - 1 < block_size) {")
    code.append("        auto output = svld1(svAll, &op[k]);")
    code.extend(compute_output(num_unrolls, InType, True))
    code.append("        svst1(svAll, &op[k], output);")
    code.append("        k += vLen;")
    code.append("      }")
    # tail loop
    code.append("      if (k < block_size) {")
    code.append("        pg = svwhilelt_b32_s64(k, block_size);")
    code.append("        auto output = svld1(pg, &op[k]);")
    code.extend(compute_output(num_unrolls, InType, False))
    code.append("        svst1(pg, &op[k], output);")
    code.append("        k += vLen;")
    code.append("      }")
    if num_unrolls == 1:
        code.append("      pos ++;")
    else:
        code.append(f"      j += {num_unrolls};")
        code.append(f"      pos += {num_unrolls};")

    code.append("    }")

    return code