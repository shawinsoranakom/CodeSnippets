async def execute_block_test(block: Block):
    prefix = f"[Test-{block.name}]"

    if not block.test_input or not block.test_output:
        log.info(f"{prefix} No test data provided")
        return
    if not isinstance(block.test_input, list):
        block.test_input = [block.test_input]
    if not isinstance(block.test_output, list):
        block.test_output = [block.test_output]

    output_index = 0
    log.info(f"{prefix} Executing {len(block.test_input)} tests...")
    prefix = " " * 4 + prefix

    for mock_name, mock_obj in (block.test_mock or {}).items():
        log.info(f"{prefix} mocking {mock_name}...")
        # check whether the field mock_name is an async function or not
        if not hasattr(block, mock_name):
            log.info(f"{prefix} mock {mock_name} not found in block")
            continue

        fun = getattr(block, mock_name)
        is_async = inspect.iscoroutinefunction(fun) or inspect.isasyncgenfunction(fun)

        if is_async:

            async def async_mock(
                *args, _mock_name=mock_name, _mock_obj=mock_obj, **kwargs
            ):
                return _mock_obj(*args, **kwargs)

            setattr(block, mock_name, async_mock)

        else:
            setattr(block, mock_name, mock_obj)

    # Populate credentials argument(s)
    # Generate IDs for execution context
    graph_id = str(uuid.uuid4())
    node_id = str(uuid.uuid4())
    graph_exec_id = str(uuid.uuid4())
    node_exec_id = str(uuid.uuid4())
    user_id = str(uuid.uuid4())
    graph_version = 1  # Default version for tests

    extra_exec_kwargs: dict = {
        "graph_id": graph_id,
        "node_id": node_id,
        "graph_exec_id": graph_exec_id,
        "node_exec_id": node_exec_id,
        "user_id": user_id,
        "graph_version": graph_version,
        "execution_context": ExecutionContext(
            user_id=user_id,
            graph_id=graph_id,
            graph_exec_id=graph_exec_id,
            graph_version=graph_version,
            node_id=node_id,
            node_exec_id=node_exec_id,
        ),
    }
    input_model = cast(type[BlockSchema], block.input_schema)

    # Handle regular credentials fields
    credentials_input_fields = input_model.get_credentials_fields()
    if len(credentials_input_fields) == 1 and isinstance(
        block.test_credentials, _BaseCredentials
    ):
        field_name = next(iter(credentials_input_fields))
        extra_exec_kwargs[field_name] = block.test_credentials
    elif credentials_input_fields and block.test_credentials:
        if not isinstance(block.test_credentials, dict):
            raise TypeError(f"Block {block.name} has no usable test credentials")
        else:
            for field_name in credentials_input_fields:
                if field_name in block.test_credentials:
                    extra_exec_kwargs[field_name] = block.test_credentials[field_name]

    # Handle auto-generated credentials (e.g., from GoogleDriveFileInput)
    auto_creds_fields = input_model.get_auto_credentials_fields()
    if auto_creds_fields and block.test_credentials:
        if isinstance(block.test_credentials, _BaseCredentials):
            # Single credentials object - use for all auto_credentials kwargs
            for kwarg_name in auto_creds_fields.keys():
                extra_exec_kwargs[kwarg_name] = block.test_credentials
        elif isinstance(block.test_credentials, dict):
            for kwarg_name in auto_creds_fields.keys():
                if kwarg_name in block.test_credentials:
                    extra_exec_kwargs[kwarg_name] = block.test_credentials[kwarg_name]

    for input_data in block.test_input:
        log.info(f"{prefix} in: {input_data}")

        async for output_name, output_data in block.execute(
            input_data, **extra_exec_kwargs
        ):
            if output_index >= len(block.test_output):
                raise ValueError(
                    f"{prefix} produced output more than expected {output_index} >= {len(block.test_output)}:\nOutput Expected:\t\t{block.test_output}\nFailed Output Produced:\t('{output_name}', {output_data})\nNote that this may not be the one that was unexpected, but it is the first that triggered the extra output warning"
                )
            ex_output_name, ex_output_data = block.test_output[output_index]

            def compare(data, expected_data):
                if data == expected_data:
                    is_matching = True
                elif isinstance(expected_data, type):
                    is_matching = isinstance(data, expected_data)
                elif callable(expected_data):
                    is_matching = expected_data(data)
                else:
                    is_matching = False

                mark = "✅" if is_matching else "❌"
                log.info(f"{prefix} {mark} comparing `{data}` vs `{expected_data}`")
                if not is_matching:
                    raise ValueError(
                        f"{prefix}: wrong output {data} vs {expected_data}\n"
                        f"Output Expected:\t\t{block.test_output}\n"
                        f"Failed Output Produced:\t('{output_name}', {output_data})"
                    )

            compare(output_data, ex_output_data)
            compare(output_name, ex_output_name)
            output_index += 1

    if output_index < len(block.test_output):
        raise ValueError(
            f"{prefix} produced output less than expected. output_index={output_index}, len(block.test_output)={len(block.test_output)}"
        )