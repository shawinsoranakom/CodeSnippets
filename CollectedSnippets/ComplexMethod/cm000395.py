async def assert_sample_graph_executions(
    test_graph: graph.Graph,
    test_user: User,
    graph_exec_id: str,
):
    logger.info(f"Checking execution results for graph {test_graph.id}")
    graph_run = await execution.get_graph_execution(
        test_user.id, graph_exec_id, include_node_executions=True
    )
    assert isinstance(graph_run, execution.GraphExecutionWithNodes)

    output_list = [{"result": ["Hello"]}, {"result": ["World"]}]
    input_list = [
        {
            "name": "input_1",
            "value": "Hello",
        },
        {
            "name": "input_2",
            "value": "World",
            "description": "This is my description of this parameter",
        },
    ]

    # Executing StoreValueBlock
    exec = graph_run.node_executions[0]
    logger.info(f"Checking first StoreValueBlock execution: {exec}")
    assert exec.status == execution.ExecutionStatus.COMPLETED
    assert exec.graph_exec_id == graph_exec_id
    assert (
        exec.output_data in output_list
    ), f"Output data: {exec.output_data} and {output_list}"
    assert (
        exec.input_data in input_list
    ), f"Input data: {exec.input_data} and {input_list}"
    assert exec.node_id in [test_graph.nodes[0].id, test_graph.nodes[1].id]

    # Executing StoreValueBlock
    exec = graph_run.node_executions[1]
    logger.info(f"Checking second StoreValueBlock execution: {exec}")
    assert exec.status == execution.ExecutionStatus.COMPLETED
    assert exec.graph_exec_id == graph_exec_id
    assert (
        exec.output_data in output_list
    ), f"Output data: {exec.output_data} and {output_list}"
    assert (
        exec.input_data in input_list
    ), f"Input data: {exec.input_data} and {input_list}"
    assert exec.node_id in [test_graph.nodes[0].id, test_graph.nodes[1].id]

    # Executing FillTextTemplateBlock
    exec = graph_run.node_executions[2]
    logger.info(f"Checking FillTextTemplateBlock execution: {exec}")
    assert exec.status == execution.ExecutionStatus.COMPLETED
    assert exec.graph_exec_id == graph_exec_id
    assert exec.output_data == {"output": ["Hello, World!!!"]}
    assert exec.input_data == {
        "format": "{{a}}, {{b}}{{c}}",
        "values": {"a": "Hello", "b": "World", "c": "!!!"},
        "values_#_a": "Hello",
        "values_#_b": "World",
        "values_#_c": "!!!",
    }
    assert exec.node_id == test_graph.nodes[2].id

    # Executing PrintToConsoleBlock
    exec = graph_run.node_executions[3]
    logger.info(f"Checking PrintToConsoleBlock execution: {exec}")
    assert exec.status == execution.ExecutionStatus.COMPLETED
    assert exec.graph_exec_id == graph_exec_id
    assert exec.output_data == {"output": ["Hello, World!!!"]}
    assert exec.input_data == {"input": "Hello, World!!!"}
    assert exec.node_id == test_graph.nodes[3].id