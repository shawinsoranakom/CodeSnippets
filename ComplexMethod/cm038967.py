async def main_mp(
    client_args: ClientArgs,
    req_args: RequestArgs,
    bench_args: BenchmarkArgs,
    tokenizer: AutoTokenizer,
    input_conv: ConversationsMap,
) -> tuple[ConversationsMap, list[RequestStats]]:
    # An event that will trigger graceful termination of all the clients
    stop_event = mp.Event()

    # Queue for input conversations (from the input file/dataset)
    task_queue: mp.Queue = mp.Queue()

    # Queue for client measurements (TTFT, TPOT, etc. for each request)
    result_queue: mp.Queue = mp.Queue()

    # Queue for output conversations (with the LLM answers, sent by the server)
    conv_queue: mp.Queue = mp.Queue()
    output_conv: ConversationsMap = {}
    client_metrics: list[RequestStats] = []

    # Start all clients
    start_time = time.perf_counter_ns()
    logger.info(f"{Color.GREEN}Starting {bench_args.num_clients} clients{Color.RESET}")

    clients = []
    for client_id in range(bench_args.num_clients):
        client = mp.Process(
            name=f"client_{client_id}",
            target=worker_function,
            args=(
                client_id,
                tokenizer,
                client_args,
                req_args,
                stop_event,
                task_queue,
                result_queue,
                conv_queue,
            ),
        )
        clients.append(client)
        client.start()

    # Submit all the input conversations as tasks for the clients
    for conv_id, messages in input_conv.items():
        task_queue.put((conv_id, messages))

    # Add termination signals for clients
    for _ in range(bench_args.num_clients):
        task_queue.put((TERM_SIGNAL, TERM_SIGNAL))

    # Collect the updated conversations from all clients
    num_clients_finished = 0
    total_convs = len(input_conv)

    debug_stats = DebugStats(logger, min(15 * bench_args.num_clients, 500))

    while num_clients_finished < bench_args.num_clients:
        # Collect updated conversation
        conv_id, messages = conv_queue.get()

        # Collect results (measurements)
        while not result_queue.empty():
            new_data = result_queue.get()
            client_metrics.append(new_data)
            debug_stats.update(new_data)

        if conv_id is TERM_SIGNAL:
            num_clients_finished += 1
            logger.info(
                f"{Color.CYAN}{num_clients_finished} out of "
                f"{bench_args.num_clients} clients finished{Color.RESET}"
            )

            if bench_args.early_stop and not stop_event.is_set():
                # Once one client finished, stop all other clients.
                # there is no reason to continue the benchmark with fewer clients.
                logger.info(
                    f"{Color.YELLOW}Sending termination signal to clients{Color.RESET}"
                )
                stop_event.set()
        else:
            output_conv[conv_id] = messages

            finished_convs = len(output_conv)
            percent = finished_convs / total_convs

            # Tuned to control the print rate (can be changed if required)
            print_cycle = max(3, int(bench_args.num_clients / 4))

            if finished_convs % print_cycle == 0:
                runtime_sec = nanosec_to_sec(time.perf_counter_ns() - start_time)
                logger.info(
                    f"{Color.CYAN}Finished {finished_convs} out of {total_convs} conversations ({percent:.0%}), "  # noqa: E501
                    f"{num_clients_finished} out of {bench_args.num_clients} clients finished, collected {len(client_metrics)} measurements, runtime {runtime_sec:.3f} sec{Color.RESET}"  # noqa: E501
                )

                rps: str | float = round(len(client_metrics) / runtime_sec, 3)
                if len(client_metrics) < (5 * bench_args.num_clients):
                    # Do not estimate the RPS if the number of samples is very low
                    # (threshold can be tuned if needed)
                    rps = "N/A"

                runtime_left_sec: str | float = round(
                    (runtime_sec / finished_convs) * (total_convs - finished_convs), 3
                )
                if percent < 0.05:
                    # If less than 5% of the conversations were not finished,
                    # the estimation will probably be very inaccurate
                    # (threshold can be tuned if needed).
                    runtime_left_sec = "N/A"

                logger.info(
                    f"{Color.CYAN}Estimated req/sec {rps}, estimated runtime left {runtime_left_sec} sec{Color.RESET}"  # noqa: E501
                )
                debug_stats.print()

    logger.info(
        f"{Color.CYAN}All {bench_args.num_clients} clients finished{Color.RESET}"
    )

    # At this point all the clients finished,
    # collect results (TTFT, TPOT, etc.) from all the clients.
    # This needs to happen before calling join on the clients
    # (result_queue should be emptied).
    while not result_queue.empty():
        client_metrics.append(result_queue.get())

    logger.info(f"Collected {len(client_metrics)} samples from all the clients")

    # Wait for all clients to finish
    for client in clients:
        logger.info(
            f"{Color.CYAN}Waiting for client {client.name} "
            f"(is alive: {client.is_alive()}){Color.RESET}"
        )

        client.join(timeout=req_args.timeout_sec + 1)

        if client.is_alive():
            logger.warning(
                f"{Color.YELLOW}Client {client.name} will be terminated{Color.RESET}"
            )
            client.terminate()

        exitcode = client.exitcode
        if exitcode != 0:
            logger.error(
                f"{Color.RED}Client {client.name} exited "
                f"with exit code {exitcode}{Color.RESET}"
            )

    logger.info(
        f"All {bench_args.num_clients} clients exited (successfully "
        f"finished {len(output_conv)} out of {total_convs} conversations)"
    )

    # Queues should be closed, required to avoid hang at interpreter shutdown
    unfinished_tasks = 0
    while not task_queue.empty():
        task_queue.get()
        unfinished_tasks += 1

    if unfinished_tasks > 0:
        # Can happen if not all tasks (conversations) have finished.
        # May happen if --max-num-requests was used,
        # or if an error occurred in one of the clients.
        logger.debug(f"Discarding {unfinished_tasks} unfinished tasks")

    task_queue.close()
    task_queue.join_thread()

    result_queue.close()
    result_queue.join_thread()

    conv_queue.close()
    conv_queue.join_thread()

    return output_conv, client_metrics