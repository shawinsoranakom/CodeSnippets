def _load_user():
    jwt = Serializer(secret_key=settings.SECRET_KEY)
    authorization = request.headers.get("Authorization")
    g.user = None
    if not authorization:
        return None

    # Extract auth_token based on whether Authorization starts with "bearer" (case-insensitive)
    if authorization.lower().startswith("bearer "):
        parts = authorization.split(maxsplit=1)
        if len(parts) < 2:
            logging.warning("Authorization header has invalid bearer format")
            return None
        auth_token = parts[1]
    else:
        auth_token = authorization

    # Try JWT decoding
    try:
        access_token = str(jwt.loads(auth_token))

        if not access_token or not access_token.strip():
            logging.warning("Authentication attempt with empty access token")
            return None

        if len(access_token.strip()) < 32:
            logging.warning(f"Authentication attempt with invalid token format: {len(access_token)} chars")
            return None

        user = UserService.query(access_token=access_token, status=StatusEnum.VALID.value)
        if user:
            if not user[0].access_token or not user[0].access_token.strip():
                logging.warning(f"User {user[0].email} has empty access_token in database")
                return None
            g.user = user[0]
            return user[0]
        return None
    except Exception as e_jwt:
        logging.warning(f"load_user from jwt got exception {e_jwt}")

    # JWT decode failed, try as api_token
    try:
        objs = APIToken.query(token=auth_token)
        if objs:
            user = UserService.query(id=objs[0].tenant_id, status=StatusEnum.VALID.value)
            if user:
                if not user[0].access_token or not user[0].access_token.strip():
                    logging.warning(f"User {user[0].email} has empty access_token in database")
                    return None
                g.user = user[0]
                return user[0]
            logging.warning(f"load_user: No user found for tenant_id={objs[0].tenant_id} from APIToken")
        else:
            logging.warning(f"load_user: No APIToken found for token={auth_token[:10]}...")
    except Exception as e_api_token:
        logging.warning(f"load_user from api token got exception {e_api_token}")

    return None