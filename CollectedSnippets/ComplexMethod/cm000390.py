def test_build_summary_with_different_error_formats(
        self, mock_execution_stats, mock_blocks
    ):
        """Test building summary with different error formats."""
        # Create node executions with different error formats and realistic UUIDs
        mock_executions = [
            NodeExecutionResult(
                user_id="test_user",
                graph_id="test_graph",
                graph_version=1,
                graph_exec_id="test_exec",
                node_exec_id="111e2222-e89b-12d3-a456-426614174010",
                node_id="333e4444-e89b-12d3-a456-426614174011",
                block_id="process_block_id",
                status=ExecutionStatus.FAILED,
                input_data={},
                output_data={"error": ["Simple string error message"]},
                add_time=datetime.now(timezone.utc),
                queue_time=None,
                start_time=None,
                end_time=None,
            ),
            NodeExecutionResult(
                user_id="test_user",
                graph_id="test_graph",
                graph_version=1,
                graph_exec_id="test_exec",
                node_exec_id="555e6666-e89b-12d3-a456-426614174012",
                node_id="777e8888-e89b-12d3-a456-426614174013",
                block_id="process_block_id",
                status=ExecutionStatus.FAILED,
                input_data={},
                output_data={},  # No error in output
                add_time=datetime.now(timezone.utc),
                queue_time=None,
                start_time=None,
                end_time=None,
            ),
        ]

        with patch(
            "backend.executor.activity_status_generator.get_block"
        ) as mock_get_block:
            mock_get_block.side_effect = lambda block_id: mock_blocks.get(block_id)

            summary = _build_execution_summary(
                mock_executions,
                mock_execution_stats,
                "Error Test Graph",
                "Testing error formats",
                [],
                ExecutionStatus.FAILED,
            )

            # Check different error formats - errors are now in nodes' recent_errors
            error_nodes = [n for n in summary["nodes"] if n.get("recent_errors")]
            assert len(error_nodes) == 2

            # String error format - find node with truncated ID
            string_error_node = next(
                n for n in summary["nodes"] if n["node_id"] == "333e4444"  # Truncated
            )
            assert len(string_error_node["recent_errors"]) == 1
            assert (
                string_error_node["recent_errors"][0]["error"]
                == "Simple string error message"
            )

            # No error output format - find node with truncated ID
            no_error_node = next(
                n for n in summary["nodes"] if n["node_id"] == "777e8888"  # Truncated
            )
            assert len(no_error_node["recent_errors"]) == 1
            assert no_error_node["recent_errors"][0]["error"] == "Unknown error"