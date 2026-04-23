def test_cli_utility_functions():
    """Test port/host/flow-ID utilities — no server involved."""
    from lfx.cli.common import (
        flow_id_from_path,
        get_best_access_host,
        get_free_port,
        is_port_in_use,
    )

    assert not is_port_in_use(0)

    port = get_free_port(8000)
    assert 8000 <= port < 65535

    assert get_best_access_host("0.0.0.0") == "localhost"
    assert get_best_access_host("") == "localhost"
    assert get_best_access_host("127.0.0.1") == "127.0.0.1"

    root = Path("/tmp/flows")
    path = root / "test.json"
    flow_id = flow_id_from_path(path, root)
    assert isinstance(flow_id, str)
    assert len(flow_id) == 36