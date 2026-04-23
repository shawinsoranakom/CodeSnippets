def bench(
    types: TypeConfig,
    group_size: int,
    m: int,
    k: int,
    n: int,
    label: str,
    sub_label: str,
    sweep_schedules: bool = True,
) -> list[TMeasurement]:
    benchmark_tensors = create_bench_tensors((m, n, k), types, group_size)
    sub_label += f", L={len(benchmark_tensors)}"

    name_type_string = f"W{types.weight_type}" + f"-A{terse_type_name(types.act_type)}"
    if types.group_scale_type is not None:
        name_type_string += f"-GS{terse_type_name(types.group_scale_type)}"
    if types.group_zero_type is not None:
        name_type_string += f"-GZ{terse_type_name(types.group_zero_type)}"
    if group_size is not None:
        name_type_string += f"-G{group_size}"
    if types.channel_scale_type is not None:
        name_type_string += f"-CS{terse_type_name(types.channel_scale_type)}"
    if types.token_scale_type is not None:
        name_type_string += f"-TS{terse_type_name(types.token_scale_type)}"

    timers = []
    # pytorch impl
    timers.append(
        bench_fns(
            label,
            sub_label,
            "torch.matmul (fp16)",
            [torch_matmul_f16_create_bench_fn(bt) for bt in benchmark_tensors],
        )
    )

    if types.act_type == torch.int8 or types.act_type == torch.float8_e4m3fn:
        timers.append(
            bench_fns(
                label,
                sub_label,
                f"cutlass_scaled_mm ({terse_type_name(types.act_type)})",
                [cutlass_scaled_mm_create_bench_fn(bt) for bt in benchmark_tensors],
            )
        )

    if types.act_type != torch.float8_e4m3fn:
        timers.append(
            bench_fns(
                label,
                sub_label,
                f"marlin ({name_type_string})",
                [marlin_create_bench_fn(bt) for bt in benchmark_tensors],
            )
        )

    # machete
    timers.append(
        bench_fns(
            label,
            sub_label,
            f"machete ({name_type_string})",
            [
                machete_create_bench_fn(bt, out_type=types.output_type)
                for bt in benchmark_tensors
            ],
        )
    )

    # cutlass w4a8
    if types.act_type == torch.float8_e4m3fn and group_size == 128:
        timers.append(
            bench_fns(
                label,
                sub_label,
                f"cutlass w4a8 ({name_type_string})",
                [
                    cutlass_w4a8_create_bench_fn(bt, out_type=types.output_type)
                    for bt in benchmark_tensors
                ],
            )
        )

    if sweep_schedules:
        global _SWEEP_SCHEDULES_RESULTS

        print("Finding best schedule for machete")
        best = None
        best_schedule = None
        schedules = ops.machete_supported_schedules(
            a_type=types.act_type,
            b_type=types.weight_type,
            group_scales_type=types.group_scale_type,
            group_zeros_type=types.group_zero_type,
            token_scales_type=types.token_scale_type,
            channel_scales_type=types.channel_scale_type,
            out_type=types.output_type,
        )

        if schedules is None or len(schedules) == 0:
            raise ValueError("No schedules found to sweep")

        for schedule in reversed(schedules):
            schedule_M = int(schedule.split("_")[0].split("x")[1])

            # Prune known bad schedules
            if schedule_M >= 2 * max(m, 16) or schedule_M < m // 4:
                continue

            res = bench_fns(
                label,
                sub_label,
                "machete_best",
                [
                    machete_create_bench_fn(
                        bt, out_type=types.output_type, schedule=schedule
                    )
                    for bt in benchmark_tensors
                ],
            )

            results_row = {
                "M": m,
                "K": k,
                "N": n,
                "group_size": group_size,
                "schedule": schedule,
                "median": res.median,
            }
            if _SWEEP_SCHEDULES_RESULTS is None:
                _SWEEP_SCHEDULES_RESULTS = pd.DataFrame(columns=results_row.keys())
            _SWEEP_SCHEDULES_RESULTS.loc[len(_SWEEP_SCHEDULES_RESULTS)] = results_row

            print(f"  {res.median:5.5} ", schedule)
            if not best or res.median < best.median:
                best = res
                best_schedule = schedule
        print("Best schedule:", best_schedule)
        timers.append(best)

    return timers