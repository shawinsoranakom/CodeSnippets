def test_get_system_info():
    """Test that get_system_info returns valid system information."""
    with patch(
        'openhands.runtime.utils.system_stats.get_system_stats'
    ) as mock_get_stats:
        mock_get_stats.return_value = {'cpu_percent': 10.0}

        info = get_system_info()

        # Test structure
        assert isinstance(info, dict)
        assert set(info.keys()) == {'uptime', 'idle_time', 'resources'}

        # Test values
        assert isinstance(info['uptime'], float)
        assert isinstance(info['idle_time'], float)
        assert info['uptime'] > 0
        assert info['idle_time'] >= 0
        assert info['resources'] == {'cpu_percent': 10.0}

        # Verify get_system_stats was called
        mock_get_stats.assert_called_once()