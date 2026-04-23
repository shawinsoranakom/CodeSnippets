async def configure_user_auto_top_up(
    request: AutoTopUpConfig, user_id: Annotated[str, Security(get_user_id)]
) -> str:
    """Configure auto top-up settings and perform an immediate top-up if needed.

    Raises HTTPException(422) if the request parameters are invalid or if
    the credit top-up fails.
    """
    if request.threshold < 0:
        raise HTTPException(status_code=422, detail="Threshold must be greater than 0")
    if request.amount < 500 and request.amount != 0:
        raise HTTPException(
            status_code=422, detail="Amount must be greater than or equal to 500"
        )
    if request.amount != 0 and request.amount < request.threshold:
        raise HTTPException(
            status_code=422, detail="Amount must be greater than or equal to threshold"
        )

    user_credit_model = await get_user_credit_model(user_id)
    current_balance = await user_credit_model.get_credits(user_id)

    try:
        if current_balance < request.threshold:
            await user_credit_model.top_up_credits(user_id, request.amount)
        else:
            await user_credit_model.top_up_credits(user_id, 0)
    except ValueError as e:
        known_messages = (
            "must not be negative",
            "already exists for user",
            "No payment method found",
        )
        if any(msg in str(e) for msg in known_messages):
            raise HTTPException(status_code=422, detail=str(e))
        raise

    try:
        await set_auto_top_up(
            user_id, AutoTopUpConfig(threshold=request.threshold, amount=request.amount)
        )
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    return "Auto top-up settings updated"