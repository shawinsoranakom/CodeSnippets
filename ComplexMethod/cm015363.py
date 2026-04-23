async def run1(coroutine_id):
    global progress

    if args.gpus == "all":
        gpuid = coroutine_id % GPUS
    else:
        gpu_assignments = args.gpus.split(":")
        if args.nproc != len(gpu_assignments):
            raise AssertionError(
                f"Please specify GPU assignment for each process, separated by : "
                f"(got {len(gpu_assignments)} assignments for {args.nproc} processes)"
            )
        gpuid = gpu_assignments[coroutine_id]

    while progress < len(ALL_TESTS):
        test = ALL_TESTS[progress]
        progress += 1
        cmd = f"CUDA_VISIBLE_DEVICES={gpuid} cuda-memcheck --error-exitcode 1 python {args.filename} {test}"
        proc = await asyncio.create_subprocess_shell(
            cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
        try:
            stdout, stderr = await asyncio.wait_for(proc.communicate(), args.timeout)
        except asyncio.TimeoutError:
            print("Timeout:", test, file=logfile)
            proc.kill()
            if args.ci and not args.nohang:
                sys.exit("Hang detected on cuda-memcheck")
        else:
            if proc.returncode == 0:
                print("Success:", test, file=logfile)
            else:
                stdout = stdout.decode()
                stderr = stderr.decode()
                should_display = args.strict or not is_ignored_only(stdout)
                if should_display:
                    print("Fail:", test, file=logfile)
                    print(stdout, file=logfile)
                    print(stderr, file=logfile)
                    if args.ci:
                        sys.exit("Failure detected on cuda-memcheck")
                else:
                    print("Ignored:", test, file=logfile)
        del proc
        progressbar.update(1)