async def test_get_monitor_transactions_does_not_return_other_users_data(
    client: AsyncClient,
    logged_in_headers,
    other_logged_in_headers,
    cross_user_monitor_data,
):
    own_response = await client.get(
        "api/v1/monitor/transactions",
        params={"flow_id": cross_user_monitor_data["owned_flow_id"]},
        headers=logged_in_headers,
    )
    assert own_response.status_code == 200, own_response.text
    assert len(own_response.json()["items"]) == 1

    foreign_response = await client.get(
        "api/v1/monitor/transactions",
        params={"flow_id": cross_user_monitor_data["foreign_flow_id"]},
        headers=logged_in_headers,
    )
    assert foreign_response.status_code == 200, foreign_response.text
    assert foreign_response.json()["items"] == []
    assert foreign_response.json()["total"] == 0

    owner_response = await client.get(
        "api/v1/monitor/transactions",
        params={"flow_id": cross_user_monitor_data["foreign_flow_id"]},
        headers=other_logged_in_headers,
    )
    assert owner_response.status_code == 200, owner_response.text
    assert len(owner_response.json()["items"]) == 1