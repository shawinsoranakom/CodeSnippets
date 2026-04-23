async def interactive_login(
        cls,
        project_id: str = "",
        no_browser: bool = False,
        timeout: float = 300.0,
    ) -> Dict[str, Any]:
        """
        Perform interactive OAuth login flow.

        This opens a browser for Google OAuth and captures the callback locally.

        Args:
            project_id: Optional GCP project ID
            no_browser: If True, don't auto-open browser (print URL instead)
            timeout: Timeout in seconds for OAuth callback

        Returns:
            Dict containing tokens and user info
        """
        # Build authorization URL
        auth_url, verifier, state = cls.build_authorization_url(project_id)

        print("\n" + "=" * 60)
        print("Antigravity OAuth Login")
        print("=" * 60)

        # Try to start local callback server
        callback_server = OAuthCallbackServer(timeout=timeout)
        server_started = callback_server.start()

        if server_started and not no_browser:
            print(f"\nOpening browser for authentication...")
            print(f"If browser doesn't open, visit this URL:\n")
            print(f"{auth_url}\n")

            # Try to open browser
            try:
                webbrowser.open(auth_url)
            except Exception as e:
                print(f"Could not open browser automatically: {e}")
                print("Please open the URL above manually.\n")
        else:
            if not server_started:
                print(f"\nCould not start local callback server on port {OAUTH_CALLBACK_PORT}.")
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

                # Exchange code for tokens
                tokens = await cls.exchange_code_for_tokens(code, callback_state or state)

                print(f"✓ Authentication successful!")
                if tokens.get("email"):
                    print(f"  Logged in as: {tokens['email']}")
                if tokens.get("project_id"):
                    print(f"  Project ID: {tokens['project_id']}")

                return tokens

            finally:
                callback_server.stop()
        else:
            # Manual flow - ask user to paste the redirect URL or code
            print("\nAfter completing authentication, you'll be redirected to a localhost URL.")
            print("Copy and paste the full redirect URL or just the authorization code below:\n")

            user_input = input("Paste redirect URL or code: ").strip()

            if not user_input:
                raise RuntimeError("No input provided")

            # Parse the input
            if user_input.startswith("http"):
                parsed = urlparse(user_input)
                params = parse_qs(parsed.query)
                code = params.get("code", [None])[0]
                callback_state = params.get("state", [state])[0]
            else:
                # Assume it's just the code
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