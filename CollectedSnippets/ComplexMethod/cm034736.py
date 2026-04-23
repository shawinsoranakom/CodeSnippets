async def interactive_login(
        cls,
        no_browser: bool = False,
        timeout: float = 300.0,
    ) -> Dict[str, Any]:
        """Perform interactive OAuth login flow."""
        auth_url, verifier, state = cls.build_authorization_url()

        print("\n" + "=" * 60)
        print("GeminiCLI OAuth Login")
        print("=" * 60)

        callback_server = GeminiCLIOAuthCallbackServer(timeout=timeout)
        server_started = callback_server.start()

        if server_started and not no_browser:
            print(f"\nOpening browser for authentication...")
            print(f"If browser doesn't open, visit this URL:\n")
            print(f"{auth_url}\n")

            try:
                webbrowser.open(auth_url)
            except Exception as e:
                print(f"Could not open browser automatically: {e}")
                print("Please open the URL above manually.\n")
        else:
            if not server_started:
                print(f"\nCould not start local callback server on port {GEMINICLI_OAUTH_CALLBACK_PORT}.")
                print("You may need to close any application using that port.\n")

            print(f"\nPlease open this URL in your browser:\n")
            print(f"{auth_url}\n")

        if server_started:
            print("Waiting for authentication callback...")

            try:
                callback_result = callback_server.wait_for_callback()

                if not callback_result:
                    raise RuntimeError("OAuth callback timed out")

                code = callback_result.get("code")
                callback_state = callback_result.get("state")

                if not code:
                    raise RuntimeError("No authorization code received")

                print("\n✓ Authorization code received. Exchanging for tokens...")

                tokens = await cls.exchange_code_for_tokens(code, callback_state or state)

                print(f"✓ Authentication successful!")
                if tokens.get("email"):
                    print(f"  Logged in as: {tokens['email']}")

                return tokens

            finally:
                callback_server.stop()
        else:
            print("\nAfter completing authentication, you'll be redirected to a localhost URL.")
            print("Copy and paste the full redirect URL or just the authorization code below:\n")

            user_input = input("Paste redirect URL or code: ").strip()

            if not user_input:
                raise RuntimeError("No input provided")

            if user_input.startswith("http"):
                parsed = urlparse(user_input)
                params = parse_qs(parsed.query)
                code = params.get("code", [None])[0]
                callback_state = params.get("state", [state])[0]
            else:
                code = user_input
                callback_state = state

            if not code:
                raise RuntimeError("Could not extract authorization code")

            print("\nExchanging code for tokens...")
            tokens = await cls.exchange_code_for_tokens(code, callback_state)

            print(f"✓ Authentication successful!")
            if tokens.get("email"):
                print(f"  Logged in as: {tokens['email']}")

            return tokens