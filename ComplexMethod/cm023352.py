async def test_delete_dataset(
    hass: HomeAssistant, hass_ws_client: WebSocketGenerator
) -> None:
    """Test we can delete a dataset."""
    assert await async_setup_component(hass, DOMAIN, {})
    await hass.async_block_till_done()

    client = await hass_ws_client(hass)

    await client.send_json_auto_id(
        {"type": "thread/add_dataset_tlv", "source": "test", "tlv": DATASET_1}
    )
    msg = await client.receive_json()
    assert msg["success"]

    await client.send_json_auto_id(
        {"type": "thread/add_dataset_tlv", "source": "test", "tlv": DATASET_2}
    )
    msg = await client.receive_json()
    assert msg["success"]

    await client.send_json_auto_id({"type": "thread/list_datasets"})
    msg = await client.receive_json()
    assert msg["success"]
    datasets = msg["result"]["datasets"]

    # Set the first dataset as preferred
    await client.send_json_auto_id(
        {
            "type": "thread/set_preferred_dataset",
            "dataset_id": datasets[0]["dataset_id"],
        }
    )
    msg = await client.receive_json()
    assert msg["success"]
    assert msg["result"] is None

    # Try deleting the preferred dataset
    await client.send_json_auto_id(
        {"type": "thread/delete_dataset", "dataset_id": datasets[0]["dataset_id"]}
    )
    msg = await client.receive_json()
    assert not msg["success"]
    assert msg["error"] == {
        "code": "not_allowed",
        "message": "attempt to remove preferred dataset",
    }

    # Try deleting a non preferred dataset
    await client.send_json_auto_id(
        {"type": "thread/delete_dataset", "dataset_id": datasets[1]["dataset_id"]}
    )
    msg = await client.receive_json()
    assert msg["success"]

    # Try deleting the same dataset again
    await client.send_json_auto_id(
        {"type": "thread/delete_dataset", "dataset_id": datasets[1]["dataset_id"]}
    )
    msg = await client.receive_json()
    assert not msg["success"]
    assert msg["error"] == {
        "code": "not_found",
        "message": f"'{datasets[1]['dataset_id']}'",
    }