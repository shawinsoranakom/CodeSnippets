async def test_process_review_action_per_review_auto_approve_granularity(
    client: httpx.AsyncClient,
    mocker: pytest_mock.MockerFixture,
    sample_pending_review: PendingHumanReviewModel,
    test_user_id: str,
) -> None:
    """Test that auto-approval can be set per-review (granular control)"""
    # Mock get_reviews_by_node_exec_ids - return different reviews based on node_exec_id
    mock_get_reviews_for_user = mocker.patch(
        "backend.api.features.executions.review.routes.get_reviews_by_node_exec_ids"
    )

    # Create a mapping of node_exec_id to review
    review_map = {
        "node_1_auto": PendingHumanReviewModel(
            node_exec_id="node_1_auto",
            user_id=test_user_id,
            graph_exec_id="test_graph_exec",
            graph_id="test_graph",
            graph_version=1,
            payload={"data": "node1"},
            instructions="Review 1",
            editable=True,
            status=ReviewStatus.WAITING,
            review_message=None,
            was_edited=False,
            processed=False,
            created_at=FIXED_NOW,
        ),
        "node_2_manual": PendingHumanReviewModel(
            node_exec_id="node_2_manual",
            user_id=test_user_id,
            graph_exec_id="test_graph_exec",
            graph_id="test_graph",
            graph_version=1,
            payload={"data": "node2"},
            instructions="Review 2",
            editable=True,
            status=ReviewStatus.WAITING,
            review_message=None,
            was_edited=False,
            processed=False,
            created_at=FIXED_NOW,
        ),
        "node_3_auto": PendingHumanReviewModel(
            node_exec_id="node_3_auto",
            user_id=test_user_id,
            graph_exec_id="test_graph_exec",
            graph_id="test_graph",
            graph_version=1,
            payload={"data": "node3"},
            instructions="Review 3",
            editable=True,
            status=ReviewStatus.WAITING,
            review_message=None,
            was_edited=False,
            processed=False,
            created_at=FIXED_NOW,
        ),
    }

    # Return the review map dict (batch function returns all requested reviews)
    mock_get_reviews_for_user.return_value = review_map

    # Mock process_all_reviews - return 3 approved reviews
    mock_process_all_reviews = mocker.patch(
        "backend.api.features.executions.review.routes.process_all_reviews_for_execution"
    )
    mock_process_all_reviews.return_value = {
        "node_1_auto": PendingHumanReviewModel(
            node_exec_id="node_1_auto",
            user_id=test_user_id,
            graph_exec_id="test_graph_exec",
            graph_id="test_graph",
            graph_version=1,
            payload={"data": "node1"},
            instructions="Review 1",
            editable=True,
            status=ReviewStatus.APPROVED,
            review_message=None,
            was_edited=False,
            processed=False,
            created_at=FIXED_NOW,
            updated_at=FIXED_NOW,
            reviewed_at=FIXED_NOW,
        ),
        "node_2_manual": PendingHumanReviewModel(
            node_exec_id="node_2_manual",
            user_id=test_user_id,
            graph_exec_id="test_graph_exec",
            graph_id="test_graph",
            graph_version=1,
            payload={"data": "node2"},
            instructions="Review 2",
            editable=True,
            status=ReviewStatus.APPROVED,
            review_message=None,
            was_edited=False,
            processed=False,
            created_at=FIXED_NOW,
            updated_at=FIXED_NOW,
            reviewed_at=FIXED_NOW,
        ),
        "node_3_auto": PendingHumanReviewModel(
            node_exec_id="node_3_auto",
            user_id=test_user_id,
            graph_exec_id="test_graph_exec",
            graph_id="test_graph",
            graph_version=1,
            payload={"data": "node3"},
            instructions="Review 3",
            editable=True,
            status=ReviewStatus.APPROVED,
            review_message=None,
            was_edited=False,
            processed=False,
            created_at=FIXED_NOW,
            updated_at=FIXED_NOW,
            reviewed_at=FIXED_NOW,
        ),
    }

    # Mock get_node_executions to return batch node data
    mock_get_node_executions = mocker.patch(
        "backend.api.features.executions.review.routes.get_node_executions"
    )
    # Create mock node executions for each review
    mock_node_execs = []
    for node_exec_id in ["node_1_auto", "node_2_manual", "node_3_auto"]:
        mock_node = mocker.Mock(spec=NodeExecutionResult)
        mock_node.node_exec_id = node_exec_id
        mock_node.node_id = f"node_def_{node_exec_id}"
        mock_node_execs.append(mock_node)
    mock_get_node_executions.return_value = mock_node_execs

    # Mock create_auto_approval_record
    mock_create_auto_approval = mocker.patch(
        "backend.api.features.executions.review.routes.create_auto_approval_record"
    )

    # Mock get_graph_execution_meta
    mock_get_graph_exec = mocker.patch(
        "backend.api.features.executions.review.routes.get_graph_execution_meta"
    )
    mock_graph_exec_meta = mocker.Mock()
    mock_graph_exec_meta.status = ExecutionStatus.REVIEW
    mock_get_graph_exec.return_value = mock_graph_exec_meta

    # Mock has_pending_reviews_for_graph_exec
    mock_has_pending = mocker.patch(
        "backend.api.features.executions.review.routes.has_pending_reviews_for_graph_exec"
    )
    mock_has_pending.return_value = False

    # Mock settings and execution
    mock_get_settings = mocker.patch(
        "backend.api.features.executions.review.routes.get_graph_settings"
    )
    mock_get_settings.return_value = GraphSettings(
        human_in_the_loop_safe_mode=False, sensitive_action_safe_mode=False
    )

    mocker.patch("backend.api.features.executions.review.routes.add_graph_execution")
    mocker.patch("backend.api.features.executions.review.routes.get_user_by_id")

    # Request with granular auto-approval:
    # - node_1_auto: auto_approve_future=True
    # - node_2_manual: auto_approve_future=False (explicit)
    # - node_3_auto: auto_approve_future=True
    request_data = {
        "reviews": [
            {
                "node_exec_id": "node_1_auto",
                "approved": True,
                "auto_approve_future": True,
            },
            {
                "node_exec_id": "node_2_manual",
                "approved": True,
                "auto_approve_future": False,  # Don't auto-approve this one
            },
            {
                "node_exec_id": "node_3_auto",
                "approved": True,
                "auto_approve_future": True,
            },
        ],
    }

    response = await client.post("/api/review/action", json=request_data)

    assert response.status_code == 200

    # Verify create_auto_approval_record was called ONLY for reviews with auto_approve_future=True
    assert mock_create_auto_approval.call_count == 2

    # Check that it was called for node_1 and node_3, but NOT node_2
    call_args_list = [call.kwargs for call in mock_create_auto_approval.call_args_list]
    node_ids_with_auto_approval = [args["node_id"] for args in call_args_list]

    assert "node_def_node_1_auto" in node_ids_with_auto_approval
    assert "node_def_node_3_auto" in node_ids_with_auto_approval
    assert "node_def_node_2_manual" not in node_ids_with_auto_approval