async def client_main(
    args: ClientArgs,
    req_args: RequestArgs,
    client_id: int,
    tokenizer: AutoTokenizer,
    stop_event: mp.Event,  # type: ignore
    task_queue: mp.Queue,
    result_queue: mp.Queue,
    conv_queue: mp.Queue,
) -> None:
    logger.info(
        f"{Color.CYAN}Started client {client_id}: max_num_requests={args.max_num_requests}, max_active_conversations={args.max_active_conversations}{Color.RESET}"  # noqa: E501
    )

    # Set unique seed per client (each client runs in its own process)
    # Add 1 to ensure no client uses the same seed as the main process
    client_seed = args.seed + client_id + 1
    random.seed(client_seed)
    np.random.seed(client_seed)

    # Active conversations
    active_convs: ConversationsMap = {}
    conv_id_queue: deque = deque(maxlen=args.max_active_conversations)

    # Keep track of how many messages have been used for each conversation
    turns_count: Counter = Counter()
    num_successes = 0
    num_failures = 0

    # Track the timestamp (time.perf_counter())
    # of the last turn per conversation (only for debug)
    time_of_last_turn: dict[ConvId, float] = {}

    # Flag that indicates that there are no new tasks (conversations) for the client
    task_queue_empty = False

    async with aiohttp.ClientSession() as session:
        # Print progress

        while task_queue_empty is False:
            result = None

            if (
                args.max_num_requests
                and num_successes + num_failures == args.max_num_requests
            ):
                logger.info(
                    f"{Color.YELLOW}Client {client_id} reached "
                    f"request limit{Color.RESET}"
                )
                break

            if stop_event.is_set():  # type: ignore
                logger.info(
                    f"{Color.YELLOW}Client {client_id} received "
                    f"a termination signal{Color.RESET}"
                )
                break

            while (
                len(active_convs) < args.max_active_conversations
                and task_queue_empty is False
            ):
                # Get a new conversation from the task queue
                conv_id, messages = task_queue.get()

                if conv_id is TERM_SIGNAL:
                    task_queue_empty = True
                    break

                if args.skip_first_turn:
                    # Skip the first turn (both user and assistant),
                    # relevant if warmup was enabled.
                    # Default turns_count[conv_id] will be zero if conv_id
                    # was never inserted/updated in turns_count.
                    turns_count[conv_id] += 2

                if turns_count[conv_id] < len(messages):
                    # Add new conversation
                    active_convs[conv_id] = messages
                    conv_id_queue.append(conv_id)

                    if args.verbose:
                        logger.info(
                            f"{Color.GREEN}Client {client_id} will use conversation ID {conv_id} (active conversations {len(active_convs)}){Color.RESET}"  # noqa: E501
                        )

                elif args.verbose:
                    # No more messages (conversation finished during the warmup)
                    logger.info(
                        f"{Color.YELLOW}Client {client_id} will not use conversation ID {conv_id} (all {len(messages)} messages already sent){Color.RESET}"  # noqa: E501
                    )

            if len(active_convs) == 0 or task_queue_empty:
                logger.info(
                    f"{Color.YELLOW}Client {client_id} has no more work{Color.RESET}"
                )
                break

            # Pick an active conversation for the next request
            if args.conversation_sampling == ConversationSampling.ROUND_ROBIN:
                conv_id = conv_id_queue.pop()
            else:
                # ConversationSampling.RANDOM
                active_ids = list(active_convs.keys())
                conv_id = random.choice(active_ids)

            messages = active_convs[conv_id]
            assert isinstance(messages, list) and len(messages) > 0

            # Update the amount of messages to use
            turns_count[conv_id] += 1
            current_turn = turns_count[conv_id]

            assert current_turn < len(messages), (
                f"Turn number {current_turn} is invalid for conversation ID {conv_id}"
                f" that has only {len(messages)} messages"
            )

            if args.verbose:
                curr_time_sec: float = time.perf_counter()
                time_since_last_turn: str | float = "N/A"
                if conv_id in time_of_last_turn:
                    time_since_last_turn = round(
                        curr_time_sec - time_of_last_turn[conv_id], 3
                    )
                logger.info(
                    f"Client {client_id} using conversation ID {conv_id} (turn: {current_turn}, time since last turn [sec]: {time_since_last_turn})"  # noqa: E501
                )
                time_of_last_turn[conv_id] = curr_time_sec

            success = False
            for attempt_cnt in range(args.max_retries + 1):
                try:
                    exception = False
                    result = await send_turn(
                        session,
                        client_id,
                        conv_id,
                        messages,
                        current_turn,
                        tokenizer,
                        req_args,
                        args.print_content,
                        args.verify_output,
                    )
                    if result is not None:
                        result_queue.put(result)
                        success = True
                        break
                    else:
                        logger.warning(
                            f"{Color.YELLOW}Client {client_id} - Request rejected during conversation ID {conv_id} (turn: {current_turn}){Color.RESET}"  # noqa: E501
                        )
                except asyncio.exceptions.TimeoutError:
                    exception = True
                    logger.error(
                        "%sClient %d - Timeout during conversation ID %s (turn: %d). "
                        "Base timeout is %ss (set with --request-timeout-sec), but the "
                        "effective timeout may be longer based on max_tokens. If this "
                        "is unexpected, consider increasing the timeout or checking "
                        "model performance.%s",
                        Color.RED,
                        client_id,
                        conv_id,
                        current_turn,
                        req_args.timeout_sec,
                        Color.RESET,
                    )
                except Exception:
                    exception = True
                    logger.exception(
                        f"{Color.RED}Client {client_id} - Exception during conversation ID {conv_id} (turn: {current_turn}){Color.RESET}"  # noqa: E501
                    )

                # Sleep before retry if not last attempt
                if not success and attempt_cnt < args.max_retries:
                    await exponential_backoff_sleep(attempt_cnt, verbose=args.verbose)

            if not success:
                num_failures += 1
                # Remove the conversation (should not be used again)
                active_convs.pop(conv_id)
                if exception:
                    break  # Exit gracefully instead of raising an error

            else:
                num_successes += 1

                # Update the turns counter to include the LLM response
                # The LLM response will be used as context for the next user turn
                turns_count[conv_id] += 1

                max_turns = len(messages)
                if args.max_turns is not None:
                    # Limit the number of turns in the conversation
                    max_turns = min(args.max_turns, max_turns)

                if turns_count[conv_id] >= max_turns:
                    # Conversation has no more turns (no longer active)
                    # save the updated conversation (with the LLM server's answer)
                    conv_queue.put((conv_id, active_convs.pop(conv_id)))
                    if args.verbose:
                        logger.info(
                            f"{Color.GREEN}Client {client_id} finished "
                            f"conversation ID {conv_id}{Color.RESET}"
                        )
                else:
                    # Conversation is not finished, insert it at the back of the queue
                    conv_id_queue.appendleft(conv_id)

            # Sleep between requests (if lambda is positive)
            if args.request_rate > 0:
                await poisson_sleep(args.request_rate, args.verbose)

    # Send indication that the client is done
    conv_queue.put((TERM_SIGNAL, TERM_SIGNAL))

    logger.info(
        f"{Color.CYAN}Client {client_id} is done "
        f"({num_successes=}, {num_failures=}){Color.RESET}"
    )