async def test_search_app_conversation_start_tasks_with_created_at_gte_filter(
        self,
        service: SQLAppConversationStartTaskService,
        sample_request: AppConversationStartRequest,
    ):
        """Test search with created_at__gte filter."""
        from datetime import timedelta

        from openhands.agent_server.models import utc_now

        # Create tasks with different creation times
        base_time = utc_now()

        # Task 1: created 2 hours ago
        task1 = AppConversationStartTask(
            id=uuid4(),
            created_by_user_id='user1',
            status=AppConversationStartTaskStatus.WORKING,
            request=sample_request,
        )
        task1.created_at = base_time - timedelta(hours=2)
        await service.save_app_conversation_start_task(task1)

        # Task 2: created 1 hour ago
        task2 = AppConversationStartTask(
            id=uuid4(),
            created_by_user_id='user1',
            status=AppConversationStartTaskStatus.READY,
            request=sample_request,
        )
        task2.created_at = base_time - timedelta(hours=1)
        await service.save_app_conversation_start_task(task2)

        # Task 3: created 30 minutes ago
        task3 = AppConversationStartTask(
            id=uuid4(),
            created_by_user_id='user1',
            status=AppConversationStartTaskStatus.WORKING,
            request=sample_request,
        )
        task3.created_at = base_time - timedelta(minutes=30)
        await service.save_app_conversation_start_task(task3)

        # Search for tasks created in the last 90 minutes
        filter_time = base_time - timedelta(minutes=90)
        result = await service.search_app_conversation_start_tasks(
            created_at__gte=filter_time
        )

        # Should return task2 and task3 (created within last 90 minutes)
        assert len(result.items) == 2
        task_ids = [task.id for task in result.items]
        assert task2.id in task_ids
        assert task3.id in task_ids
        assert task1.id not in task_ids

        # Test count with the same filter
        count = await service.count_app_conversation_start_tasks(
            created_at__gte=filter_time
        )
        assert count == 2

        # Search for tasks created in the last 45 minutes
        filter_time_recent = base_time - timedelta(minutes=45)
        result_recent = await service.search_app_conversation_start_tasks(
            created_at__gte=filter_time_recent
        )

        # Should return only task3
        assert len(result_recent.items) == 1
        assert result_recent.items[0].id == task3.id

        # Test count with recent filter
        count_recent = await service.count_app_conversation_start_tasks(
            created_at__gte=filter_time_recent
        )
        assert count_recent == 1