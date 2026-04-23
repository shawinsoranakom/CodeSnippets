async def on_options_load(request: Request, background_tasks: BackgroundTasks):
    """Handle external_select options loading (block_suggestion payload).

    This endpoint is called by Slack when a user interacts with an external_select
    element. It supports dynamic repository search with pagination.

    The endpoint:
    1. Authenticates the Slack user
    2. Searches for repositories matching the user's query
    3. Returns up to 100 options for the dropdown

    Note: "No Repository" is handled by a separate button in the form, so it's
    not included in the dropdown options. Error cases return an empty list.

    Configuration: Set the Options Load URL in Slack App settings to:
    https://your-domain/slack/on-options-load
    """
    if not SLACK_WEBHOOKS_ENABLED:
        return JSONResponse({'options': []})

    body = await request.body()
    form = await request.form()
    payload_str = form.get('payload')
    if not payload_str:
        logger.warning('slack_on_options_load: No payload in request')
        return JSONResponse({'options': []})

    payload = json.loads(payload_str)

    logger.info('slack_on_options_load', extra={'payload': payload})

    # Verify the signature
    if not signature_verifier.is_valid(
        body=body,
        timestamp=request.headers.get('X-Slack-Request-Timestamp'),
        signature=request.headers.get('X-Slack-Signature'),
    ):
        raise HTTPException(status_code=403, detail='invalid_request')

    # Verify this is a block_suggestion payload
    if payload.get('type') != 'block_suggestion':
        logger.warning(
            f"slack_on_options_load: Unexpected payload type: {payload.get('type')}"
        )
        return JSONResponse({'options': []})

    slack_user_id = payload['user']['id']
    search_value = payload.get('value', '')  # What user typed in the search box

    # Authenticate user
    slack_user, saas_user_auth = await slack_manager.authenticate_user(slack_user_id)

    if not slack_user or not saas_user_auth:
        # Send ephemeral message asking user to link their account
        background_tasks.add_task(
            slack_manager.handle_slack_error,
            payload,
            SlackError(
                SlackErrorCode.USER_NOT_AUTHENTICATED,
                message_kwargs={'login_link': _generate_login_link()},
                log_context={'slack_user_id': slack_user_id},
            ),
        )
        return JSONResponse({'options': []})

    try:
        # Search for repositories matching the query
        # Limit to 20 repos for fast initial load. Users can search for repos
        # not in this list using the type-ahead search functionality.
        options = await slack_manager.search_repos_for_slack(
            saas_user_auth, query=search_value, per_page=20
        )

        logger.info(
            'slack_on_options_load_success',
            extra={
                'slack_user_id': slack_user_id,
                'search_value': search_value,
                'num_options': len(options),
            },
        )

        return JSONResponse({'options': options})

    except ProviderTimeoutError as e:
        # Handle provider timeout with user notification
        background_tasks.add_task(
            slack_manager.handle_slack_error,
            payload,
            SlackError(
                SlackErrorCode.PROVIDER_TIMEOUT,
                log_context={'slack_user_id': slack_user_id, 'error': str(e)},
            ),
        )
        return JSONResponse({'options': []})

    except Exception as e:
        logger.exception(
            'slack_options_load_error',
            extra={
                'slack_user_id': slack_user_id,
                'search_value': search_value,
                'error': str(e),
            },
        )
        # Notify user about the unexpected error with error code
        background_tasks.add_task(
            slack_manager.handle_slack_error,
            payload,
            SlackError(
                SlackErrorCode.UNEXPECTED_ERROR,
                log_context={'slack_user_id': slack_user_id, 'error': str(e)},
            ),
        )
        return JSONResponse({'options': []})