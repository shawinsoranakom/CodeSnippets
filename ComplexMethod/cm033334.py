async def forget_reset_password():
    """
    Reset password after successful OTP verification.
    Requires: { email, new_password, confirm_new_password }
    Steps:
    - check verified flag in Redis
    - update user password
    - auto login
    - clear verified flag
    """

    req = await get_request_json()
    email = req.get("email") or ""
    new_pwd = req.get("new_password")
    new_pwd2 = req.get("confirm_new_password")

    new_pwd_base64 = decrypt(new_pwd)
    new_pwd_string = base64.b64decode(new_pwd_base64).decode('utf-8')
    new_pwd2_string = base64.b64decode(decrypt(new_pwd2)).decode('utf-8')

    if not REDIS_CONN.get(_verified_key(email)):
        return get_json_result(data=False, code=RetCode.AUTHENTICATION_ERROR, message="email not verified")

    if not all([email, new_pwd, new_pwd2]):
        return get_json_result(data=False, code=RetCode.ARGUMENT_ERROR, message="email and passwords are required")

    if new_pwd_string != new_pwd2_string:
        return get_json_result(data=False, code=RetCode.ARGUMENT_ERROR, message="passwords do not match")

    users = UserService.query_user_by_email(email=email)
    if not users:
        return get_json_result(data=False, code=RetCode.DATA_ERROR, message="invalid email")

    user = users[0]
    try:
        UserService.update_user_password(user.id, new_pwd_base64)
    except Exception as e:
        logging.exception(e)
        return get_json_result(data=False, code=RetCode.EXCEPTION_ERROR, message="failed to reset password")

    # clear verified flag
    try:
        REDIS_CONN.delete(_verified_key(email))
    except Exception:
        pass

    msg = "Password reset successful. Logged in."
    return await construct_response(data=user.to_json(), auth=user.get_id(), message=msg)