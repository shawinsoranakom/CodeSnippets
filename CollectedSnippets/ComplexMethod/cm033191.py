def load_user(web_request):
        # Authorization header contains JWT-encoded access token
        # First decode JWT to get the UUID, then query database
        from itsdangerous.url_safe import URLSafeTimedSerializer as Serializer
        from common import settings

        authorization = web_request.headers.get("Authorization")
        if authorization:
            try:
                # Strip "Bearer " prefix if present
                jwt_token = authorization
                if jwt_token.startswith("Bearer "):
                    jwt_token = jwt_token[7:]

                jwt_token = jwt_token.strip()
                if not jwt_token:
                    logging.warning("Authentication attempt with empty JWT token")
                    return None

                # Decode JWT to get the UUID access_token
                jwt = Serializer(secret_key=settings.SECRET_KEY)
                access_token = str(jwt.loads(jwt_token))

                if not access_token or not access_token.strip():
                    logging.warning("Authentication attempt with empty access token after JWT decode")
                    return None

                # Access tokens stored in database are UUIDs (32 hex characters)
                if len(access_token) < 32:
                    logging.warning(f"Authentication attempt with invalid token format: {len(access_token)} chars")
                    return None

                user = UserService.query(
                    access_token=access_token, status=StatusEnum.VALID.value
                )
                if user:
                    if not user[0].access_token or not user[0].access_token.strip():
                        logging.warning(f"User {user[0].email} has empty access_token in database")
                        return None
                    return user[0]
                else:
                    return None
            except Exception as e:
                logging.warning(f"load_user got exception {e}")
                return None
        else:
            return None