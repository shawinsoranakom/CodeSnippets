def run_with_input_iter(bench_cls, input_iter, allow_skip=True):
        tensor_dim_specs = input_iter.split(",")
        tensor_dim_specs = [dim.split(":") for dim in tensor_dim_specs]

        configs = []
        for start, stop, inc in tensor_dim_specs:
            dim_list = []
            if inc == "pow2":
                curr = int(start)
                while curr <= int(stop):
                    dim_list.append(curr)
                    curr <<= 1
            elif inc == "pow2+1":
                curr = int(start)
                while curr <= int(stop):
                    dim_list.append(curr)
                    curr -= 1
                    curr <<= 1
                    curr += 1
            else:
                dim_list = list(range(int(start), int(stop) + int(inc), int(inc)))
            configs.append(dim_list)
        configs = itertools.product(*configs)

        for mode, device, dtype, config in itertools.product(
            modes, devices, datatypes, list(configs)
        ):
            bench = bench_cls(mode, device, dtype, *config)
            bench.output_type = args.output
            bench.jit_mode = args.jit_mode
            if not bench.is_supported():
                if allow_skip:
                    continue
                else:
                    raise ValueError(
                        f"attempted to run an unsupported benchmark: {bench.desc()}"
                    )
            bench.run(args)