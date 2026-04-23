def build_model(self) -> LanguageModel:
        try:
            from langchain_google_vertexai import ChatVertexAI
        except ImportError as e:
            msg = "Please install the langchain-google-vertexai package to use the VertexAIEmbeddings component."
            raise ImportError(msg) from e
        location = self.location or None
        if self.credentials:
            from google.cloud import aiplatform
            from google.oauth2 import service_account

            credentials = service_account.Credentials.from_service_account_file(self.credentials)
            project = self.project or credentials.project_id
            # ChatVertexAI sometimes skip manual credentials initialization
            aiplatform.init(
                project=project,
                location=location,
                credentials=credentials,
            )
        else:
            project = self.project or None
            credentials = None

        return cast(
            "LanguageModel",
            ChatVertexAI(
                credentials=credentials,
                location=location,
                project=project,
                max_output_tokens=self.max_output_tokens or None,
                max_retries=self.max_retries,
                model_name=self.model_name,
                temperature=self.temperature,
                top_k=self.top_k or None,
                top_p=self.top_p,
                verbose=self.verbose,
            ),
        )