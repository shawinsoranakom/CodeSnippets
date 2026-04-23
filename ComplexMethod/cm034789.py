async def authorization(request: Request, call_next):
            user = None
            if request.method != "OPTIONS" and AppConfig.g4f_api_key is not None or AppConfig.demo:
                update_authorization = False
                try:
                    user_g4f_api_key = await self.get_g4f_api_key(request)
                except HTTPException:
                    user_g4f_api_key = getattr(await self.security(request), "credentials", None)
                    update_authorization = True
                if user_g4f_api_key:
                    user_g4f_api_key = user_g4f_api_key.split()
                country = request.headers.get("Cf-Ipcountry", "")
                if AppConfig.demo and user is None:
                    ip = request.headers.get("X-Forwarded-For", "")[:4].strip(":.")
                    user = request.headers.get("x-user", ip)
                    user = f"{country}:{user}" if country else user
                if AppConfig.g4f_api_key is None or not user_g4f_api_key or not secrets.compare_digest(AppConfig.g4f_api_key, user_g4f_api_key[0]):
                    if has_crypto and user_g4f_api_key:
                        try:
                            expires, user = decrypt_data(private_key, user_g4f_api_key[0]).split(":", 1)
                        except Exception:
                            try:
                                data = json.loads(decrypt_data(session_key, user_g4f_api_key[0]))
                                debug.log(f"Decrypted G4F API key data: {data}")
                                expires = int(decrypt_data(private_key, data.pop("data"))) + 86400
                                user = data.get("user", user)
                                if not user or "referrer" not in data:
                                    raise ValueError("User not found")
                            except Exception:
                                return ErrorResponse.from_message(f"Invalid G4F API key", HTTP_401_UNAUTHORIZED)
                        user = f"{country}:{user}" if country else user
                        expires = int(expires) - int(time.time())
                        hours, remainder = divmod(expires, 3600)
                        minutes, seconds = divmod(remainder, 60)
                        if expires < 0:
                            debug.log(f"G4F API key expired for user '{user}'")
                            return ErrorResponse.from_message("G4F API key expired", HTTP_401_UNAUTHORIZED)
                        count = 0
                        for char in user:
                            if char.isupper():
                                count += 1
                        if count >= 6:
                            debug.log(f"Invalid user name (screaming): '{user}'")
                            return ErrorResponse.from_message("Invalid user name (screaming)", HTTP_401_UNAUTHORIZED)
                        debug.log(f"User: '{user}' G4F API key expires in {hours}h {minutes}m {seconds}s")
                else:
                    user = "admin"
                path = request.url.path
                if _requires_api_key(path, AppConfig.demo):
                    if request.method != "OPTIONS" and not path.endswith("/models"):
                        if not user_g4f_api_key:
                            return ErrorResponse.from_message("G4F API key required", HTTP_401_UNAUTHORIZED)
                        if AppConfig.g4f_api_key is None and user is None:
                            return ErrorResponse.from_message("Invalid G4F API key", HTTP_403_FORBIDDEN)
                elif not AppConfig.demo and not path.startswith("/images/") and not path.startswith("/media/"):
                    if user_g4f_api_key:
                        if user is None:
                            return ErrorResponse.from_message("Invalid G4F API key", HTTP_403_FORBIDDEN)
                    elif path.startswith("/backend-api/") or path.startswith("/chat/"):
                        try:
                            user = await self.get_username(request)
                        except HTTPException as e:
                            return ErrorResponse.from_message(e.detail, e.status_code, e.headers)
                if user_g4f_api_key and update_authorization:
                    new_api_key = user_g4f_api_key.pop()
                    if secrets.compare_digest(AppConfig.g4f_api_key, new_api_key):
                        new_api_key = None
                else:
                    new_api_key = None
                request = update_headers(request, new_api_key, user)
            response = await call_next(request)
            return response