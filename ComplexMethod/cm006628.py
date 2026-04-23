def test_update_template(sample_template, sample_nodes):
    # Making a deep copy to keep original sample_nodes unchanged
    nodes_copy = copy.deepcopy(sample_nodes)
    update_template(sample_template, nodes_copy)

    # Now, validate the updates.
    node1_updated = next((n for n in nodes_copy if n["id"] == "node1"), None)
    node2_updated = next((n for n in nodes_copy if n["id"] == "node2"), None)
    node3_updated = next((n for n in nodes_copy if n["id"] == "node3"), None)

    assert node1_updated["data"]["node"]["template"]["some_field"]["show"] is True
    assert node1_updated["data"]["node"]["template"]["some_field"]["advanced"] is False
    assert node1_updated["data"]["node"]["template"]["some_field"]["display_name"] == "Name1"

    assert node2_updated["data"]["node"]["template"]["other_field"]["show"] is False
    assert node2_updated["data"]["node"]["template"]["other_field"]["advanced"] is True
    assert node2_updated["data"]["node"]["template"]["other_field"]["display_name"] == "DisplayName2"

    # Ensure node3 remains unchanged
    assert node3_updated == sample_nodes[2]