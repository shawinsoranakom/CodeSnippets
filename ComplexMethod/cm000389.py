def test_build_summary_with_failed_execution(
        self, mock_node_executions, mock_execution_stats, mock_blocks
    ):
        """Test building summary for execution with failures."""
        mock_links = []  # No links for this test

        with patch(
            "backend.executor.activity_status_generator.get_block"
        ) as mock_get_block:
            mock_get_block.side_effect = lambda block_id: mock_blocks.get(block_id)

            summary = _build_execution_summary(
                mock_node_executions,
                mock_execution_stats,
                "Failed Graph",
                "Test with failures",
                mock_links,
                ExecutionStatus.FAILED,
            )

            # Check that errors are now in node's recent_errors field
            # Find the output node (with truncated UUID)
            output_node = next(
                n for n in summary["nodes"] if n["node_id"] == "678e9012"  # Truncated
            )
            assert output_node["error_count"] == 1
            assert output_node["execution_count"] == 1

            # Check recent_errors field
            assert "recent_errors" in output_node
            assert len(output_node["recent_errors"]) == 1
            assert (
                output_node["recent_errors"][0]["error"]
                == "Connection timeout: Unable to reach external service"
            )
            assert (
                "execution_id" in output_node["recent_errors"][0]
            )