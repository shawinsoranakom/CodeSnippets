def run_script(services: list[str], path: None):
    """send requests against all APIs"""
    print(
        f"writing results to '{path}implementation_coverage_full.csv' and '{path}implementation_coverage_aggregated.csv'..."
    )
    with (
        open(f"{path}implementation_coverage_full.csv", "w") as csvfile,
        open(f"{path}implementation_coverage_aggregated.csv", "w") as aggregatefile,
    ):
        full_w = csv.DictWriter(
            csvfile,
            fieldnames=[
                "service",
                "operation",
                "status_code",
                "error_code",
                "error_message",
                "is_implemented",
            ],
        )
        aggregated_w = csv.DictWriter(
            aggregatefile,
            fieldnames=["service", "implemented_count", "full_count", "percentage"],
        )

        full_w.writeheader()
        aggregated_w.writeheader()

        total_count = 0
        for service_name in services:
            service = service_models.get(service_name)
            for op_name in service.operation_names:
                if op_name in PHANTOM_OPERATIONS.get(service_name, []):
                    continue
                total_count += 1

        time_start = time.perf_counter_ns()
        counter = 0
        responses = {}
        for service_name in services:
            c.print(f"\n=====  {service_name} =====")
            service = service_models.get(service_name)
            for op_name in service.operation_names:
                if op_name in PHANTOM_OPERATIONS.get(service_name, []):
                    continue
                counter += 1
                c.print(
                    f"{100 * counter / total_count:3.1f}% | Calling endpoint {counter:4.0f}/{total_count}: {service_name}.{op_name}"
                )

                # here's the important part (the actual service call!)
                response = simulate_call(service_name, op_name)

                responses.setdefault(service_name, {})[op_name] = response
                is_implemented = str(not map_to_notimplemented(response))
                full_w.writerow(response | {"is_implemented": is_implemented})

            # calculate aggregate for service
            all_count = len(responses[service_name].values())
            implemented_count = len(
                [r for r in responses[service_name].values() if not map_to_notimplemented(r)]
            )
            implemented_percentage = implemented_count / all_count

            aggregated_w.writerow(
                {
                    "service": response["service"],
                    "implemented_count": implemented_count,
                    "full_count": all_count,
                    "percentage": f"{implemented_percentage * 100:.1f}",
                }
            )
        time_end = time.perf_counter_ns()
        delta = timedelta(microseconds=(time_end - time_start) / 1000.0)
        c.print(f"\n\nDone.\nTotal time to completion: {delta}")