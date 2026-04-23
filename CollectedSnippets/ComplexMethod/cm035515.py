def test_merge_conversation_stats_duplicates_overwrite_and_log_errors(
    mock_file_store, self_side, other_side
):
    stats_a = ConversationStats(
        file_store=mock_file_store, conversation_id='conv-merge-a', user_id='user-x'
    )
    stats_b = ConversationStats(
        file_store=mock_file_store, conversation_id='conv-merge-b', user_id='user-x'
    )

    # Place the same service id on the specified sides
    dupe_id = 'dupe-service'
    m1 = Metrics(model_name='m')
    m1.add_cost(0.1)  # ensure not dropped
    m2 = Metrics(model_name='m')
    m2.add_cost(0.2)  # ensure not dropped

    if self_side == 'active':
        stats_a.service_to_metrics[dupe_id] = m1
    else:
        stats_a.restored_metrics[dupe_id] = m1

    if other_side == 'active':
        stats_b.service_to_metrics[dupe_id] = m2
    else:
        stats_b.restored_metrics[dupe_id] = m2

    # Perform merge; should not raise and should log error internally if active metrics present
    stats_a.merge_and_save(stats_b)

    # Only restored metrics are merged; duplicates are allowed with incoming overwriting
    if other_side == 'restored':
        assert dupe_id in stats_a.restored_metrics
        assert stats_a.restored_metrics[dupe_id] is m2  # incoming overwrites existing
    else:
        # No restored metric came from incoming; existing restored stays as-is
        if self_side == 'restored':
            assert dupe_id in stats_a.restored_metrics
            assert stats_a.restored_metrics[dupe_id] is m1
        else:
            assert dupe_id not in stats_a.restored_metrics