def generic(IndexType, InType, OutType, use_weights, isa, fused, use_offsets):
    def compute(InType, use_weights, isa):
        code = []
        if InType == "float":
            code.append(
                "          _mm256_storeu_ps(\n"
                "              &op[j],\n"
                "              _mm256_fmadd_ps(\n"
                "                  vwgt, _mm256_loadu_ps(&ip[j]), _mm256_loadu_ps(&op[j])));"
            )
        elif InType == "at::Half":
            code.append(
                "          _mm256_storeu_ps(\n"
                "              &op[j],\n"
                "              _mm256_fmadd_ps(\n"
                "                  vwgt,\n"
                "                  _mm256_cvtph_ps(_mm_loadu_si128(\n"
                "                      reinterpret_cast<const __m128i*>(&ip[j]))),\n"
                "                  _mm256_loadu_ps(&op[j])));"
            )
        elif InType == "at::BFloat16":
            code.append(
                "          _mm256_storeu_ps(\n"
                "              &op[j],\n"
                "              _mm256_fmadd_ps(\n"
                "                  vwgt,\n"
                "                  _mm256_castsi256_ps(_mm256_slli_epi32(\n"
                "                      _mm256_cvtepu16_epi32(_mm_loadu_si128(\n"
                "                          reinterpret_cast<const __m128i*>(&ip[j]))),\n"
                "                      16)),\n"
                "                  _mm256_loadu_ps(&op[j])));"
            )
        elif InType == "uint8_t":
            code.append(
                "          _mm256_storeu_ps(\n"
                "              &op[j],\n"
                "              _mm256_fmadd_ps(\n"
                "                  vwgt,\n"
                "                  _mm256_cvtepi32_ps(_mm256_cvtepu8_epi32(_mm_loadl_epi64(\n"
                "                      reinterpret_cast<const __m128i*>(&ip[j])))),\n"
                "                  _mm256_add_ps(_mm256_loadu_ps(&op[j]), vbio)));"
            )
        else:
            raise AssertionError

        code.append(
            "          _mm_prefetch(\n"
            "              reinterpret_cast<const char*>(&ip_next_T0[j]), _MM_HINT_T0);"
        )

        return code

    code = []
    if InType == "at::Half":
        code.append("    alignas(64) at::Half vtmp1[8] = {0};")
    if InType == "at::BFloat16":
        code.append("    alignas(64) at::BFloat16 vtmp1[8] = {0};")

    if use_offsets:
        code.append(
            "    for ("
            + IndexType
            + " rangeIndex = 0; rangeIndex < output_size; ++rangeIndex) {"
        )
    else:
        code.append(
            "    for ("
            + IndexType
            + " rangeIndex = 0; rangeIndex < output_size; ++rangeIndex) {"
        )

    code.append("      " + OutType + "* op = &out[rangeIndex * block_size];")

    # initialize to 0
    code.append("      int64_t j = 0;")
    code.append("      for (; j + 8 <= block_size; j += 8) {")
    code.append("        _mm256_storeu_ps(op + j, _mm256_setzero_ps());")
    code.append("      }")
    code.append("      for (; j < block_size; j++) {")
    code.append("        op[j] = 0.0f;")
    code.append("      }")

    # inner loop
    if use_offsets:
        code.append(
            "      if (dataInd != offsets[rangeIndex] - offsets[0]) {\n"
            + "        return false;\n"
            + "      }"
        )
        code.append("""\
      int64_t end_offset = offsets[rangeIndex + 1];
      int64_t length = end_offset - offsets[rangeIndex];""")
        code.append(
            "      for ("
            + "int64_t"
            + " start = dataInd; dataInd < end_offset - offsets[0];\n           ++dataInd) {"
        )
    else:
        code.append(
            "      if (dataInd + lengths[rangeIndex] > index_size) {\n"
            + "        return false;\n"
            + "      }"
        )
        code.append(
            "      for ("
            + IndexType
            + " start = dataInd; dataInd < start + lengths[rangeIndex];\n           ++dataInd) {"
        )
    code.append("        const " + IndexType + " idx = indices[dataInd];")
    code.append(
        "        if (idx < 0 || idx >= data_size) {\n"
        + "          return false;\n"
        + "        }"
    )

    if InType == "uint8_t":
        code.append("        " + OutType + " wgt = 1.f;")
        code.append("        if (weights) {")
        code.append(
            "          wgt = weights[IS_WEIGHT_POSITIONAL ? (dataInd - start) : dataInd];"
        )
        code.append("        }")
        if fused:
            code.append(
                "        const float* scale_bias = reinterpret_cast<const float*>(\n"
                "            &input[idx * fused_block_size + block_size]);"
            )
            code.append("        " + OutType + " bio = wgt * scale_bias[1];")
            code.append("        wgt = wgt * scale_bias[0];")
        else:
            code.append("        " + OutType + " bio = wgt * scale_bias[2 * idx + 1];")
            code.append("        wgt = wgt * scale_bias[2 * idx];")
        code.append("        __m256 vbio = _mm256_set1_ps(bio);")
    else:
        code.append("        " + OutType + " wgt = 1.f;")
        code.append("        if (weights) {")
        code.append(
            "          wgt = weights[IS_WEIGHT_POSITIONAL ? (dataInd - start) : dataInd];"
        )
        code.append("        }")
    code.append("        __m256 vwgt = _mm256_set1_ps(wgt);")

    code.append(f"        const {InType}* ip = &input[idx * fused_block_size];")
    code.append(
        f"        const {IndexType} next_T0 = (dataInd < index_size - prefdist_T0)\n"
        "            // NOLINTNEXTLINE(cppcoreguidelines-narrowing-conversions,bugprone-narrowing-conversions)\n"
        "            ? (dataInd + prefdist_T0)\n"
        "            // NOLINTNEXTLINE(cppcoreguidelines-narrowing-conversions,bugprone-narrowing-conversions)\n"
        "            : dataInd;"
    )
    code.append("        const " + IndexType + " idx_pref_T0 = indices[next_T0];")
    code.append(
        "        if (idx_pref_T0 < 0 || idx_pref_T0 >= data_size) {\n"
        + "          return false;\n"
        + "        }"
    )
    code.append(
        f"        const {InType}* ip_next_T0 = "
        "&input[idx_pref_T0 * fused_block_size];"
    )

    # compute and store main loop
    code.append("        j = 0;")
    code.append("        for (; j + 8 <= block_size; j += 8) {")
    code.extend(compute(InType, use_weights, isa))
    code.append("        }")
    # leftover
    code.append("        for (; j < block_size; j++) {")
    if InType == "float":
        code.append("          op[j] = std::fma(wgt, ip[j], op[j]);")
    elif InType == "at::Half":
        code.append("          vtmp1[0] = ip[j];")
        code.append(
            "          __m256 vtmp2 =\n"
            "              _mm256_cvtph_ps(*(reinterpret_cast<const __m128i*>(vtmp1)));"
        )
        code.append("          op[j] = std::fma(wgt, ((float*)(&vtmp2))[0], op[j]);")
    elif InType == "at::BFloat16":
        code.append("          vtmp1[0] = ip[j];")
        code.append(
            "          __m256 vtmp2 = _mm256_castsi256_ps(_mm256_slli_epi32(\n"
            "              _mm256_cvtepu16_epi32(*(reinterpret_cast<const __m128i*>(vtmp1))),\n"
            "              16));"
        )
        code.append("          op[j] = std::fma(wgt, ((float*)(&vtmp2))[0], op[j]);")
    elif InType == "uint8_t":
        code.append("          op[j] = std::fma(wgt, (float)ip[j], bio + op[j]);")
    else:
        raise AssertionError

    code.append("        }")

    code.append("      }")

    if use_offsets:
        code.append("      if (normalize_by_lengths && length) {")
        code.append("        float len_inv = 1.0f / length;")
    else:
        code.append("      if (normalize_by_lengths && lengths[rangeIndex]) {")
        code.append("        float len_inv = 1.0f / lengths[rangeIndex];")
    code.append("        __m256 vlen_inv = _mm256_set1_ps(len_inv);")
    code.append("        j = 0;")
    code.append("        for (; j + 8 <= block_size; j += 8) {")
    code.append(
        "          _mm256_storeu_ps(\n"
        "              &op[j], _mm256_mul_ps(_mm256_loadu_ps(&op[j]), vlen_inv));"
    )
    code.append("        }")
    code.append("        for (; j < block_size; j++) {")
    code.append("          op[j] = len_inv * op[j];")
    code.append("        }")

    code.append("      }")

    code.append("    }")
    return code