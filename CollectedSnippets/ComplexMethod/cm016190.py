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