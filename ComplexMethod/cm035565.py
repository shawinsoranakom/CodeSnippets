async def test_update_task_status(
        self,
        service: SQLAppConversationStartTaskService,
        sample_task: AppConversationStartTask,
    ):
        """Test updating a task's status."""
        # Save initial task
        await service.save_app_conversation_start_task(sample_task)

        # Update the task status
        sample_task.status = AppConversationStartTaskStatus.READY
        sample_task.app_conversation_id = uuid4()
        sample_task.sandbox_id = 'test_sandbox'
        sample_task.agent_server_url = 'http://localhost:8000'

        # Save the updated task
        updated_task = await service.save_app_conversation_start_task(sample_task)

        # Verify the update
        assert updated_task.status == AppConversationStartTaskStatus.READY
        assert updated_task.app_conversation_id == sample_task.app_conversation_id
        assert updated_task.sandbox_id == 'test_sandbox'
        assert updated_task.agent_server_url == 'http://localhost:8000'

        # Retrieve and verify persistence
        retrieved_task = await service.get_app_conversation_start_task(sample_task.id)
        assert retrieved_task is not None
        assert retrieved_task.status == AppConversationStartTaskStatus.READY
        assert retrieved_task.app_conversation_id == sample_task.app_conversation_id