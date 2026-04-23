async def forget_verify_otp():
    """
    Verify email + OTP only. On success:
    - consume the OTP and attempt counters
    - set a short-lived verified flag in Redis for the email
    Request JSON: { email, otp }
    """
    req = await get_request_json()
    email = req.get("email") or ""
    otp = (req.get("otp") or "").strip()

    if not all([email, otp]):
        return get_json_result(data=False, code=RetCode.ARGUMENT_ERROR, message="email and otp are required")

    users = UserService.query(email=email)
    if not users:
        return get_json_result(data=False, code=RetCode.DATA_ERROR, message="invalid email")

    # Verify OTP from Redis
    k_code, k_attempts, k_last, k_lock = otp_keys(email)
    if REDIS_CONN.get(k_lock):
        return get_json_result(data=False, code=RetCode.NOT_EFFECTIVE, message="too many attempts, try later")

    stored = REDIS_CONN.get(k_code)
    if not stored:
        return get_json_result(data=False, code=RetCode.NOT_EFFECTIVE, message="expired otp")

    try:
        stored_hash, salt_hex = str(stored).split(":", 1)
        salt = bytes.fromhex(salt_hex)
    except Exception:
        return get_json_result(data=False, code=RetCode.EXCEPTION_ERROR, message="otp storage corrupted")

    calc = hash_code(otp.upper(), salt)
    if calc != stored_hash:
        # bump attempts
        try:
            attempts = int(REDIS_CONN.get(k_attempts) or 0) + 1
        except Exception:
            attempts = 1
        REDIS_CONN.set(k_attempts, attempts, OTP_TTL_SECONDS)
        if attempts >= ATTEMPT_LIMIT:
            REDIS_CONN.set(k_lock, int(time.time()), ATTEMPT_LOCK_SECONDS)
        return get_json_result(data=False, code=RetCode.AUTHENTICATION_ERROR, message="expired otp")

    # Success: consume OTP and attempts; mark verified
    REDIS_CONN.delete(k_code)
    REDIS_CONN.delete(k_attempts)
    REDIS_CONN.delete(k_last)
    REDIS_CONN.delete(k_lock)

    # set verified flag with limited TTL, reuse OTP_TTL_SECONDS or smaller window
    try:
        REDIS_CONN.set(_verified_key(email), "1", OTP_TTL_SECONDS)
    except Exception:
        return get_json_result(data=False, code=RetCode.SERVER_ERROR, message="failed to set verification state")

    return get_json_result(data=True, code=RetCode.SUCCESS, message="otp verified")