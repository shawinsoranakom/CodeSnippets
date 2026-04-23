def test_basic_normalization(self):
        """Queue item should be normalized to job dict."""
        item = (
            10,  # priority/number
            'prompt-123',  # prompt_id
            {'nodes': {}},  # prompt
            {
                'create_time': 1234567890,
                'extra_pnginfo': {'workflow': {'id': 'workflow-abc'}}
            },  # extra_data
            ['node1'],  # outputs_to_execute
        )
        job = normalize_queue_item(item, JobStatus.PENDING)

        assert job['id'] == 'prompt-123'
        assert job['status'] == 'pending'
        assert job['priority'] == 10
        assert job['create_time'] == 1234567890
        assert 'execution_start_time' not in job
        assert 'execution_end_time' not in job
        assert 'execution_error' not in job
        assert 'preview_output' not in job
        assert job['outputs_count'] == 0
        assert job['workflow_id'] == 'workflow-abc'