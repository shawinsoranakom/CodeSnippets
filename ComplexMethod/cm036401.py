def test_build_kv_connector_stats_with_multiple_connectors(self):
        """Test reconstruction with multiple connector types that have custom stats."""
        serialized_data = {
            "NixlConnector": {
                "data": {
                    "transfer_duration": [1.5],
                    "post_duration": [0.1],
                    "bytes_transferred": [1024],
                    "num_descriptors": [10],
                    "num_failed_transfers": [],
                    "num_failed_notifications": [],
                }
            },
            "MockConnector": {"data": {"mock_field": [1, 2, 3]}},
        }

        stats = MultiConnector.build_kv_connector_stats(data=serialized_data)

        assert stats is not None
        assert isinstance(stats, MultiKVConnectorStats)
        # Both connectors should be reconstructed
        assert len(stats.data) == 2
        assert "NixlConnector" in stats.data
        assert "MockConnector" in stats.data
        assert isinstance(stats.data["NixlConnector"], NixlKVConnectorStats)
        assert isinstance(stats.data["MockConnector"], MockConnectorStats)
        # Verify data is preserved
        assert stats.data["MockConnector"].data == {"mock_field": [1, 2, 3]}