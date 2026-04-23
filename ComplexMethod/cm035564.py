async def test_save_and_get_task(
        self,
        service: SQLAppConversationStartTaskService,
        sample_task: AppConversationStartTask,
    ):
        """Test saving and retrieving a single task."""
        # Save the task
        saved_task = await service.save_app_conversation_start_task(sample_task)

        # Verify the task was saved correctly
        assert saved_task.id == sample_task.id
        assert saved_task.created_by_user_id == sample_task.created_by_user_id
        assert saved_task.status == sample_task.status
        assert saved_task.request == sample_task.request

        # Retrieve the task
        retrieved_task = await service.get_app_conversation_start_task(sample_task.id)

        # Verify the retrieved task matches
        assert retrieved_task is not None
        assert retrieved_task.id == sample_task.id
        assert retrieved_task.created_by_user_id == sample_task.created_by_user_id
        assert retrieved_task.status == sample_task.status
        assert retrieved_task.request == sample_task.request