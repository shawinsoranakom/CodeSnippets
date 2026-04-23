def test_client_ticket_api_surface() -> None:
    """Reproduce the exact import path from the ticket spec."""
    # from langflow_sdk import Client
    # client = Client("https://langflow.example.com", api_key="...")
    # should have .list_flows(), .get_flow(), .run_flow()
    client = Client("https://langflow.example.com", api_key="test-key")  # pragma: allowlist secret
    assert hasattr(client, "list_flows")
    assert hasattr(client, "get_flow")
    assert hasattr(client, "run_flow")
    assert hasattr(client, "create_flow")
    assert hasattr(client, "update_flow")
    assert hasattr(client, "delete_flow")
    assert hasattr(client, "upsert_flow")
    client.close()