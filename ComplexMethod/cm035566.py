async def test_search_app_conversation_start_tasks_pagination(
        self,
        service: SQLAppConversationStartTaskService,
        sample_request: AppConversationStartRequest,
    ):
        """Test search with pagination."""
        # Create multiple tasks
        tasks = []
        for i in range(5):
            task = AppConversationStartTask(
                id=uuid4(),
                created_by_user_id='user1',
                status=AppConversationStartTaskStatus.WORKING,
                request=sample_request,
            )
            tasks.append(task)
            await service.save_app_conversation_start_task(task)

        # Test first page with limit 2
        result_page1 = await service.search_app_conversation_start_tasks(limit=2)
        assert len(result_page1.items) == 2
        assert result_page1.next_page_id == '2'

        # Test second page
        result_page2 = await service.search_app_conversation_start_tasks(
            page_id='2', limit=2
        )
        assert len(result_page2.items) == 2
        assert result_page2.next_page_id == '4'

        # Test last page
        result_page3 = await service.search_app_conversation_start_tasks(
            page_id='4', limit=2
        )
        assert len(result_page3.items) == 1
        assert result_page3.next_page_id is None