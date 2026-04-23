async def test_create_checkout_session_success(
    async_session_maker, mock_checkout_request, test_org
):
    """Test successful creation of checkout session."""
    mock_session = MagicMock()
    mock_session.url = 'https://checkout.stripe.com/test-session'
    mock_session.id = 'test_session_id_checkout'
    mock_create = AsyncMock(return_value=mock_session)

    mock_customer_info = {'customer_id': 'mock-customer', 'org_id': test_org.id}

    with (
        patch('stripe.checkout.Session.create_async', mock_create),
        patch('server.routes.billing.a_session_maker', async_session_maker),
        patch('integrations.stripe_service.a_session_maker', async_session_maker),
        patch(
            'integrations.stripe_service.find_or_create_customer_by_user_id',
            AsyncMock(return_value=mock_customer_info),
        ),
        patch('server.routes.billing.validate_billing_enabled'),
    ):
        result = await create_checkout_session(
            CreateCheckoutSessionRequest(amount=25), mock_checkout_request, 'mock_user'
        )

        assert isinstance(result, CreateBillingSessionResponse)
        assert result.redirect_url == 'https://checkout.stripe.com/test-session'

        # Verify Stripe session creation parameters
        mock_create.assert_called_once_with(
            customer='mock-customer',
            line_items=[
                {
                    'price_data': {
                        'unit_amount': 2500,
                        'currency': 'usd',
                        'product_data': {
                            'name': 'OpenHands Credits',
                            'tax_code': 'txcd_10000000',
                        },
                        'tax_behavior': 'exclusive',
                    },
                    'quantity': 1,
                }
            ],
            mode='payment',
            payment_method_types=['card'],
            saved_payment_method_options={'payment_method_save': 'enabled'},
            success_url='https://test.com/api/billing/success?session_id={CHECKOUT_SESSION_ID}',
            cancel_url='https://test.com/api/billing/cancel?session_id={CHECKOUT_SESSION_ID}',
        )

        # Verify database record was created
        async with async_session_maker() as session:
            result_db = await session.execute(
                select(BillingSession).where(
                    BillingSession.id == 'test_session_id_checkout'
                )
            )
            billing_session = result_db.scalar_one_or_none()
            assert billing_session is not None
            assert billing_session.user_id == 'mock_user'
            assert billing_session.org_id == test_org.id
            assert billing_session.status == 'in_progress'
            assert float(billing_session.price) == 25.0