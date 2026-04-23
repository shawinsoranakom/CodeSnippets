def _check_gpu_kernel_causality(events: list[dict]) -> list[Violation]:
    """For each (cudaLaunchKernel, GPU kernel) pair matched by External id,
    the GPU kernel must start at or after its cudaLaunchKernel."""
    cpu_launches: dict[int, dict] = {}
    gpu_kernels: dict[int, dict] = {}

    for ev in events:
        if ev.get("ph") != "X":
            continue
        args = ev.get("args", {})
        ext_id = args.get("External id")
        if ext_id is None:
            continue
        ext_id = int(ext_id)
        cat, name, ts = ev.get("cat", ""), ev.get("name", ""), float(ev.get("ts", 0))
        corr = args.get("correlation")

        if cat == "cuda_runtime" and name == "cudaLaunchKernel":
            if ext_id not in cpu_launches or ts < cpu_launches[ext_id]["ts"]:
                cpu_launches[ext_id] = {"ts": ts, "name": name, "corr": corr}
        elif cat == "kernel":
            if ext_id not in gpu_kernels or ts < gpu_kernels[ext_id]["ts"]:
                gpu_kernels[ext_id] = {"ts": ts, "name": name, "corr": corr}

    violations = []
    for ext_id, gpu in gpu_kernels.items():
        launch = cpu_launches.get(ext_id)
        if launch is None:
            continue
        if gpu["ts"] < launch["ts"]:
            skew = launch["ts"] - gpu["ts"]
            violations.append(
                Violation(
                    rule_name="_check_gpu_kernel_causality",
                    message=(
                        f"GPU kernel '{gpu['name']}' (External id={ext_id}, "
                        f"correlation={gpu['corr']}) starts {skew:.1f}us before "
                        f"its cudaLaunchKernel (External id={ext_id}, "
                        f"correlation={launch['corr']}), "
                        f"gpu_ts={gpu['ts']:.1f}, cpu_ts={launch['ts']:.1f}"
                    ),
                )
            )
    return violations