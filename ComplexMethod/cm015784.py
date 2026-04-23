def check_onnx_opset_operator(
    model, ops, opset_version=GLOBALS.export_onnx_opset_version
):
    # check_onnx_components
    if not (
        model.producer_name == producer_name
        and model.producer_version == producer_version
        and model.opset_import[0].version == opset_version
    ):
        raise AssertionError(
            f"Model metadata mismatch: producer_name={model.producer_name!r} (expected {producer_name!r}), "
            f"producer_version={model.producer_version!r} (expected {producer_version!r}), "
            f"opset_version={model.opset_import[0].version} (expected {opset_version})"
        )

    # check the schema with the onnx checker
    onnx.checker.check_model(model)

    # check target type and attributes
    graph = model.graph
    # ops should contain an object for each node
    # in graph.node, in the right order.
    # At least the op_name should be specified,
    # but the op's attributes can optionally be
    # specified as well
    if len(ops) != len(graph.node):
        raise AssertionError(f"Expected {len(ops)} ops, got {len(graph.node)}")
    for i in range(len(ops)):
        if graph.node[i].op_type != ops[i]["op_name"]:
            raise AssertionError(
                f"Expected op {ops[i]['op_name']}, got {graph.node[i].op_type}"
            )
        if "attributes" in ops[i]:
            attributes = ops[i]["attributes"]
            if len(attributes) != len(graph.node[i].attribute):
                raise AssertionError(
                    f"Expected {len(attributes)} attributes, got {len(graph.node[i].attribute)}"
                )
            for j in range(len(attributes)):
                for attribute_field in attributes[j]:
                    actual = getattr(graph.node[i].attribute[j], attribute_field)
                    if attributes[j][attribute_field] != actual:
                        raise AssertionError(
                            f"Attribute {attribute_field!r} mismatch on node {i}, attribute {j}: "
                            f"expected {attributes[j][attribute_field]!r}, got {actual!r}"
                        )