def print_results(results: list[Experiment], save_path: str | None = None):
    table_data = defaultdict(list)
    for experiment in results:
        backends = experiment.config.backends + ["flex"]
        for key, value in experiment.asdict().items():
            if key in backends:
                if value.fwd_time:
                    table_data[f"fwd_{key}"].append(float(value.fwd_time))
                if value.bwd_time:
                    table_data[f"bwd_{key}"].append(float(value.bwd_time))
            else:
                table_data[key].append(value)

    # Calculate speedups
    for backend in results[0].config.backends:
        fwd_speedups = [
            calculate_speedup(r.results["flex"], r.results[backend], type="fwd")
            for r in results
        ]
        table_data[f"fwd_speedup_flex_over_{backend}"] = fwd_speedups

    if results[0].config.calculate_bwd_time:
        for backend in results[0].config.backends:
            bwd_speedups = [
                calculate_speedup(r.results["flex"], r.results[backend], type="bwd")
                for r in results
            ]
            table_data[f"bwd_speedup_flex_over_{backend}"] = bwd_speedups

    # Calculate mem + computational throughput
    if results[0].config.cal_bandwidth:
        fwd_bandwidth = [
            calculate_bandwidth(r.config, r.results["flex"], type="fwd")
            for r in results
        ]
        table_data["fwd_mem_bw (TB/s)"] = fwd_bandwidth
        fwd_tflops = [calculate_tflops(r.config, r.results["flex"]) for r in results]
        table_data["TFlops/s"] = fwd_tflops

    print(tabulate(table_data, headers="keys", tablefmt="github", floatfmt=".3f"))

    for backend in results[0].config.backends:
        if np.isnan(table_data[f"fwd_speedup_flex_over_{backend}"]).all():
            continue
        print("\n")
        print(f"FWD Speedup of Flex over {backend}".center(125, "="))
        print("\n")
        average_data = get_average_speedups(results, type="fwd", backend=backend)
        print(tabulate(average_data, headers="keys", tablefmt="github", floatfmt=".3f"))

        if results[0].config.calculate_bwd_time:
            print("\n")
            print(f"BWD Speedup of Flex over {backend}".center(125, "="))
            print("\n")
            average_data = get_average_speedups(results, type="bwd", backend=backend)
            print(
                tabulate(
                    average_data, headers="keys", tablefmt="github", floatfmt=".3f"
                )
            )

    if save_path is not None:
        with open(save_path, "w", newline="") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=table_data.keys())
            writer.writeheader()
            for i in range(len(next(iter(table_data.values())))):
                row = {k: v[i] for k, v in table_data.items()}
                writer.writerow(row)
        print(f"\nResults saved to {save_path}")