async def test_get_messages_does_not_return_other_users_messages(
    client: AsyncClient, logged_in_headers, other_logged_in_headers, cross_user_messages
):
    response = await client.get("api/v1/monitor/messages", headers=logged_in_headers)
    assert response.status_code == 200, response.text
    returned_ids = {message["id"] for message in response.json()}
    assert str(cross_user_messages["owned_message"].id) in returned_ids
    assert str(cross_user_messages["foreign_message"].id) not in returned_ids

    other_response = await client.get("api/v1/monitor/messages", headers=other_logged_in_headers)
    assert other_response.status_code == 200, other_response.text
    other_returned_ids = {message["id"] for message in other_response.json()}
    assert str(cross_user_messages["foreign_message"].id) in other_returned_ids
    assert str(cross_user_messages["owned_message"].id) not in other_returned_ids