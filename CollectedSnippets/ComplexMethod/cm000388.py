def test_build_summary_with_successful_execution(
        self, mock_node_executions, mock_execution_stats, mock_blocks
    ):
        """Test building summary for successful execution."""
        # Create mock links with realistic UUIDs
        mock_links = [
            MagicMock(
                source_id="456e7890-e89b-12d3-a456-426614174002",
                sink_id="567e8901-e89b-12d3-a456-426614174005",
                source_name="output",
                sink_name="input",
                is_static=False,
            )
        ]

        with patch(
            "backend.executor.activity_status_generator.get_block"
        ) as mock_get_block:
            mock_get_block.side_effect = lambda block_id: mock_blocks.get(block_id)

            summary = _build_execution_summary(
                mock_node_executions[:2],
                mock_execution_stats,
                "Test Graph",
                "A test graph for processing",
                mock_links,
                ExecutionStatus.COMPLETED,
            )

            # Check graph info
            assert summary["graph_info"]["name"] == "Test Graph"
            assert summary["graph_info"]["description"] == "A test graph for processing"

            # Check nodes with per-node counts
            assert len(summary["nodes"]) == 2
            assert summary["nodes"][0]["block_name"] == "AgentInputBlock"
            assert summary["nodes"][0]["execution_count"] == 1
            assert summary["nodes"][0]["error_count"] == 0
            assert summary["nodes"][1]["block_name"] == "ProcessingBlock"
            assert summary["nodes"][1]["execution_count"] == 1
            assert summary["nodes"][1]["error_count"] == 0

            # Check node relations (UUIDs are truncated to first segment)
            assert len(summary["node_relations"]) == 1
            assert (
                summary["node_relations"][0]["source_node_id"] == "456e7890"
            )  # Truncated
            assert (
                summary["node_relations"][0]["sink_node_id"] == "567e8901"
            )  # Truncated
            assert (
                summary["node_relations"][0]["source_block_name"] == "AgentInputBlock"
            )
            assert summary["node_relations"][0]["sink_block_name"] == "ProcessingBlock"

            # Check overall status
            assert summary["overall_status"]["total_nodes_in_graph"] == 2
            assert summary["overall_status"]["total_executions"] == 3
            assert summary["overall_status"]["total_errors"] == 1
            assert summary["overall_status"]["execution_time_seconds"] == 2.5
            assert summary["overall_status"]["graph_execution_status"] == "COMPLETED"

            # Check input/output data (using actual node UUIDs)
            assert (
                "456e7890-e89b-12d3-a456-426614174002_inputs"
                in summary["input_output_data"]
            )
            assert (
                "456e7890-e89b-12d3-a456-426614174002_outputs"
                in summary["input_output_data"]
            )