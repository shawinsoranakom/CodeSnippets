def generate_commands(args, dtypes, suites, devices, compilers, output_dir):
    mode = get_mode(args)
    suites_str = "_".join(suites)
    devices_str = "_".join(devices)
    dtypes_str = "_".join(dtypes)
    compilers_str = "_".join(compilers)
    generated_file = (
        f"run_{mode}_{devices_str}_{dtypes_str}_{suites_str}_{compilers_str}.sh"
    )
    with open(generated_file, "w") as runfile:
        lines = []

        lines.append("#!/bin/bash")
        lines.append("set -x")
        lines.append("# Setup the output directory")
        if not args.keep_output_dir:
            lines.append(f"rm -rf {output_dir}")
        # It's ok if the output directory already exists
        lines.append(f"mkdir -p {output_dir}")
        lines.append("")

        for testing in ["performance", "accuracy"]:
            for iter in itertools.product(suites, devices, dtypes):
                suite, device, dtype = iter
                lines.append(
                    f"# Commands for {suite} for device={device}, dtype={dtype} for {mode} and for {testing} testing"
                )
                info = TABLE[mode]
                for compiler in compilers:
                    base_cmd = info[compiler]
                    output_filename = f"{output_dir}/{generate_csv_name(args, dtype, suite, device, compiler, testing)}"
                    launcher_cmd = "python"
                    if args.enable_cpu_launcher:
                        launcher_cmd = f"python -m torch.backends.xeon.run_cpu {args.cpu_launcher_args}"
                    cmd = f"{launcher_cmd} benchmarks/dynamo/{suite}.py --{testing} --{dtype} -d{device} --output={output_filename}"
                    cmd = f"{cmd} {base_cmd} {args.extra_args} --dashboard"
                    skip_tests_str = get_skip_tests(suite, device, args.training)
                    cmd = f"{cmd} {skip_tests_str}"

                    if args.log_operator_inputs:
                        cmd = f"{cmd} --log-operator-inputs"

                    if args.quick:
                        filters = DEFAULTS["quick"][suite]
                        cmd = f"{cmd} {filters}"

                    if (
                        compiler
                        in (
                            "inductor",
                            "inductor_no_cudagraphs",
                        )
                        and not args.no_cold_start_latency
                    ):
                        cmd = f"{cmd} --cold-start-latency"

                    if args.batch_size is not None:
                        cmd = f"{cmd} --batch-size {args.batch_size}"

                    if args.threads is not None:
                        cmd = f"{cmd} --threads {args.threads}"

                    if args.total_partitions is not None:
                        cmd = f"{cmd} --total-partitions {args.total_partitions}"

                    if args.partition_id is not None:
                        cmd = f"{cmd} --partition-id {args.partition_id}"

                    if args.inductor_compile_mode is not None:
                        cmd = f"{cmd} --inductor-compile-mode {args.inductor_compile_mode}"
                    lines.append(cmd)
                lines.append("")
        runfile.writelines([line + "\n" for line in lines])
    return generated_file