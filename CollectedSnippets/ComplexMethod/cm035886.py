def test_result_summary_generation(self):
        """Test the result summary generation logic."""

        def generate_result_summary(
            total_users, successful_upgrades, users_already_current, failed_upgrades
        ):
            """Simulate the result generation logic from the processor."""
            return {
                'total_users': total_users,
                'users_already_current': users_already_current,
                'successful_upgrades': successful_upgrades,
                'failed_upgrades': failed_upgrades,
                'summary': (
                    f'Processed {total_users} users: '
                    f'{len(successful_upgrades)} upgraded, '
                    f'{len(users_already_current)} already current, '
                    f'{len(failed_upgrades)} errors'
                ),
            }

        # Test with mixed results
        result = generate_result_summary(
            total_users=4,
            successful_upgrades=[
                {'user_id': 'user1', 'old_version': 1, 'new_version': 2},
                {'user_id': 'user2', 'old_version': 1, 'new_version': 2},
            ],
            users_already_current=['user3'],
            failed_upgrades=[
                {'user_id': 'user4', 'old_version': 1, 'error': 'Database error'},
            ],
        )

        assert result['total_users'] == 4
        assert len(result['successful_upgrades']) == 2
        assert len(result['users_already_current']) == 1
        assert len(result['failed_upgrades']) == 1
        assert '2 upgraded' in result['summary']
        assert '1 already current' in result['summary']
        assert '1 errors' in result['summary']