def test_that_outputs_cache_is_set_to_false_in_cycle():
    text_input = TextInputComponent(_id="text_input")
    router = ConditionalRouterComponent(_id="router")
    concat_component = Concatenate(_id="concatenate")
    text_input.set(input_value=router.false_response)
    concat_component.set(text=text_input.text_response)
    router.set(
        input_text=text_input.text_response,
        match_text="testtesttesttest",
        operator="equals",
        true_case_message=concat_component.concatenate,
        false_case_message=concat_component.concatenate,
    )
    text_output = TextOutputComponent(_id="text_output")
    text_output.set(input_value=router.true_response)
    chat_output = ChatOutput(_id="chat_output")
    chat_output.set(input_value=text_output.text_response)

    graph = Graph(text_input, chat_output)
    cycle_vertices = find_cycle_vertices(graph._get_edges_as_list_of_tuples())
    cycle_outputs_lists = [
        graph.vertex_map[vertex_id].custom_component._outputs_map.values() for vertex_id in cycle_vertices
    ]
    cycle_outputs = [output for outputs in cycle_outputs_lists for output in outputs]
    for output in cycle_outputs:
        assert output.cache is False

    non_cycle_outputs_lists = [
        vertex.custom_component.outputs for vertex in graph.vertices if vertex.id not in cycle_vertices
    ]
    non_cycle_outputs = [output for outputs in non_cycle_outputs_lists for output in outputs]
    for output in non_cycle_outputs:
        assert output.cache is True