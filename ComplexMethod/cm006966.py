def build_output(self) -> Data:
        self.validate_scopes(self.scopes)

        user_scopes = [scope.strip() for scope in self.scopes.split(",")]
        if self.scopes:
            scopes = user_scopes
        else:
            error_message = "Incorrect scope, check the scopes field."
            raise ValueError(error_message)

        creds = None
        token_path = Path("token.json")

        if token_path.exists():
            creds = Credentials.from_authorized_user_file(str(token_path), scopes)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if self.oauth_credentials:
                    client_secret_file = self.oauth_credentials
                else:
                    error_message = "OAuth 2.0 Credentials file not provided."
                    raise ValueError(error_message)

                flow = InstalledAppFlow.from_client_secrets_file(client_secret_file, scopes)
                creds = flow.run_local_server(port=0)

                token_path.write_text(creds.to_json(), encoding="utf-8")

        creds_json = json.loads(creds.to_json())

        return Data(data=creds_json)