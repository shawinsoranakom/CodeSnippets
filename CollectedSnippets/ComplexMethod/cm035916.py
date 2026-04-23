async def test_create_customer_stores_id_in_db(
    async_session_maker, session_maker_with_minimal_fixtures
):
    """Test that create_customer stores the customer ID in the database"""

    # Add test org and user to the db
    test_user_id, test_org_id = add_test_org_and_user(
        session_maker_with_minimal_fixtures
    )

    # Set up the mock for stripe.Customer.search_async and create_async
    mock_search = AsyncMock(return_value=MagicMock(data=[]))
    mock_create_async = AsyncMock(return_value=stripe.Customer(id='cus_test123'))

    # Create a mock org object to return from OrgStore
    mock_org = MagicMock()
    mock_org.id = test_org_id
    mock_org.contact_email = 'testy@tester.com'

    with (
        patch('integrations.stripe_service.a_session_maker', async_session_maker),
        patch('storage.org_store.a_session_maker', async_session_maker),
        patch('stripe.Customer.search_async', mock_search),
        patch('stripe.Customer.create_async', mock_create_async),
        patch(
            'integrations.stripe_service.OrgStore.get_current_org_from_keycloak_user_id',
            new_callable=AsyncMock,
        ) as mock_get_org,
        patch(
            'integrations.stripe_service.find_customer_id_by_org_id',
            new_callable=AsyncMock,
        ) as mock_find_customer,
    ):
        # Mock the async method to return the org
        mock_get_org.return_value = mock_org
        # Mock find_customer_id_by_org_id to return None (force creation path)
        mock_find_customer.return_value = None

        # Call the function
        result = await find_or_create_customer_by_user_id(str(test_user_id))

    # Verify the result
    assert result == {'customer_id': 'cus_test123', 'org_id': str(test_org_id)}

    # Verify that the stripe customer was stored in the db
    async with async_session_maker() as session:
        from sqlalchemy import select

        stmt = select(StripeCustomer).where(
            StripeCustomer.keycloak_user_id == str(test_user_id)
        )
        result = await session.execute(stmt)
        customer = result.scalar_one_or_none()
        assert customer is not None
        assert customer.id > 0
        assert customer.keycloak_user_id == str(test_user_id)
        assert customer.org_id == test_org_id
        assert customer.stripe_customer_id == 'cus_test123'
        assert customer.created_at is not None
        assert customer.updated_at is not None