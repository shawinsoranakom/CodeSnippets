async def test_returns_paginated_financial_data_with_individual_budget(
        self, org_id, mock_org_member
    ):
        """
        GIVEN: Organization with members having individual budget limits
        WHEN: get_org_members_financial_data is called
        THEN: Returns financial data using individual spend for current_budget calc
        """
        # Arrange
        user_id_str = str(mock_org_member.user_id)
        litellm_data = {
            'team_max_budget': 1000.0,
            'team_spend': 200.0,
            'members': {
                user_id_str: {'spend': 125.50, 'max_budget': 500.0}  # Individual budget
            },
        }

        with (
            patch(
                'server.services.org_member_financial_service.OrgMemberStore.get_org_members_paginated',
                new_callable=AsyncMock,
            ) as mock_get_paginated,
            patch(
                'server.services.org_member_financial_service.LiteLlmManager.get_team_members_financial_data',
                new_callable=AsyncMock,
            ) as mock_get_financial,
        ):
            mock_get_paginated.return_value = ([mock_org_member], 1)
            mock_get_financial.return_value = litellm_data

            # Act
            result = await OrgMemberFinancialService.get_org_members_financial_data(
                org_id=org_id,
                page_id=None,
                limit=10,
            )

            # Assert
            assert isinstance(result, OrgMemberFinancialPage)
            assert len(result.items) == 1
            assert result.items[0].user_id == user_id_str
            assert result.items[0].email == 'test@example.com'
            assert result.items[0].lifetime_spend == 125.50
            assert result.items[0].max_budget == 500.0
            # Individual budget: 500 - 125.50 = 374.50
            assert result.items[0].current_budget == 374.50
            assert result.current_page == 1
            assert result.per_page == 10