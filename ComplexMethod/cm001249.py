async def test_store_agents_cache_delete(self):
        """Test that specific agent list cache entries can be deleted."""
        # Mock the database function
        mock_response = StoreAgentsResponse(
            agents=[
                StoreAgent(
                    slug="test-agent",
                    agent_name="Test Agent",
                    agent_image="https://example.com/image.jpg",
                    creator="testuser",
                    creator_avatar="https://example.com/avatar.jpg",
                    sub_heading="Test subheading",
                    description="Test description",
                    runs=100,
                    rating=4.5,
                    agent_graph_id="test-graph-id",
                )
            ],
            pagination=Pagination(
                total_items=1,
                total_pages=1,
                current_page=1,
                page_size=20,
            ),
        )

        with patch(
            "backend.api.features.store.db.get_store_agents",
            new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_db:
            # Clear cache first
            store_cache._get_cached_store_agents.cache_clear()

            # First call - should hit database
            result1 = await store_cache._get_cached_store_agents(
                featured=False,
                creator=None,
                sorted_by=None,
                search_query="test",
                category=None,
                page=1,
                page_size=20,
            )
            assert mock_db.call_count == 1
            assert result1.agents[0].agent_name == "Test Agent"

            # Second call with same params - should use cache
            await store_cache._get_cached_store_agents(
                featured=False,
                creator=None,
                sorted_by=None,
                search_query="test",
                category=None,
                page=1,
                page_size=20,
            )
            assert mock_db.call_count == 1  # No additional DB call

            # Third call with different params - should hit database
            await store_cache._get_cached_store_agents(
                featured=True,  # Different param
                creator=None,
                sorted_by=None,
                search_query="test",
                category=None,
                page=1,
                page_size=20,
            )
            assert mock_db.call_count == 2  # New DB call

            # Delete specific cache entry
            deleted = store_cache._get_cached_store_agents.cache_delete(
                featured=False,
                creator=None,
                sorted_by=None,
                search_query="test",
                category=None,
                page=1,
                page_size=20,
            )
            assert deleted is True  # Entry was deleted

            # Try to delete non-existent entry
            deleted = store_cache._get_cached_store_agents.cache_delete(
                featured=False,
                creator="nonexistent",
                sorted_by=None,
                search_query="test",
                category=None,
                page=1,
                page_size=20,
            )
            assert deleted is False  # Entry didn't exist

            # Call with deleted params - should hit database again
            await store_cache._get_cached_store_agents(
                featured=False,
                creator=None,
                sorted_by=None,
                search_query="test",
                category=None,
                page=1,
                page_size=20,
            )
            assert mock_db.call_count == 3  # New DB call after deletion

            # Call with featured=True - should still be cached
            await store_cache._get_cached_store_agents(
                featured=True,
                creator=None,
                sorted_by=None,
                search_query="test",
                category=None,
                page=1,
                page_size=20,
            )
            assert mock_db.call_count == 3