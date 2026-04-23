def run_benchmark(client: RAGFlowClient, command_dict: dict):
    concurrency = command_dict.get("concurrency", 1)
    iterations = command_dict.get("iterations", 1)
    command: dict = command_dict["command"]
    command.update({"iterations": iterations})

    command_type = command["type"]
    if concurrency < 1:
        print("Concurrency must be greater than 0")
        return
    elif concurrency == 1:
        result = run_command(client, command)
        success_count: int = 0
        response_list = result["response_list"]
        for response in response_list:
            match command_type:
                case "ping_server":
                    if response.status_code == 200:
                        success_count += 1
                case _:
                    res_json = response.json()
                    if response.status_code == 200 and res_json["code"] == 0:
                        success_count += 1

        total_duration = result["duration"]
        qps = iterations / total_duration if total_duration > 0 else None
        print(f"command: {command}, Concurrency: {concurrency}, iterations: {iterations}")
        print(
            f"total duration: {total_duration:.4f}s, QPS: {qps}, COMMAND_COUNT: {iterations}, SUCCESS: {success_count}, FAILURE: {iterations - success_count}")
        pass
    else:
        results: List[Optional[dict]] = [None] * concurrency
        mp_context = mp.get_context("spawn")
        start_time = time.perf_counter()
        with ProcessPoolExecutor(max_workers=concurrency, mp_context=mp_context) as executor:
            future_map = {
                executor.submit(
                    run_command,
                    client,
                    command
                ): idx
                for idx in range(concurrency)
            }
            for future in as_completed(future_map):
                idx = future_map[future]
                results[idx] = future.result()
        end_time = time.perf_counter()
        success_count = 0
        for result in results:
            response_list = result["response_list"]
            for response in response_list:
                match command_type:
                    case "ping_server":
                        if response.status_code == 200:
                            success_count += 1
                    case _:
                        res_json = response.json()
                        if response.status_code == 200 and res_json["code"] == 0:
                            success_count += 1

        total_duration = end_time - start_time
        total_command_count = iterations * concurrency
        qps = total_command_count / total_duration if total_duration > 0 else None
        print(f"command: {command}, Concurrency: {concurrency} , iterations: {iterations}")
        print(
            f"total duration: {total_duration:.4f}s, QPS: {qps}, COMMAND_COUNT: {total_command_count}, SUCCESS: {success_count}, FAILURE: {total_command_count - success_count}")

    pass