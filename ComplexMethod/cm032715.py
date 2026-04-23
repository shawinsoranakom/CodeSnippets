def _construct_completion_args(self, history, stream: bool, tools: bool, **kwargs):
        completion_args = {
            "model": self.model_name,
            "messages": history,
            "api_key": self.api_key,
            "num_retries": self.max_retries,
            **kwargs,
        }
        if stream:
            completion_args.update(
                {
                    "stream": stream,
                }
            )
        if tools and self.tools:
            completion_args.update(
                {
                    "tools": self.tools,
                    "tool_choice": "auto",
                }
            )
        if self.provider in FACTORY_DEFAULT_BASE_URL:
            completion_args.update({"api_base": self.base_url})
        elif self.provider == SupportedLiteLLMProvider.Bedrock:
            import boto3

            completion_args.pop("api_key", None)
            completion_args.pop("api_base", None)

            bedrock_key = json.loads(self.api_key)
            mode = bedrock_key.get("auth_mode")
            if not mode:
                logging.error("Bedrock auth_mode is not provided in the key")
                raise ValueError("Bedrock auth_mode must be provided in the key")

            bedrock_region = bedrock_key.get("bedrock_region")

            if mode == "access_key_secret":
                completion_args.update({"aws_region_name": bedrock_region})
                completion_args.update({"aws_access_key_id": bedrock_key.get("bedrock_ak")})
                completion_args.update({"aws_secret_access_key": bedrock_key.get("bedrock_sk")})
            elif mode == "iam_role":
                aws_role_arn = bedrock_key.get("aws_role_arn")
                sts_client = boto3.client("sts", region_name=bedrock_region)
                resp = sts_client.assume_role(RoleArn=aws_role_arn, RoleSessionName="BedrockSession")
                creds = resp["Credentials"]
                completion_args.update({"aws_region_name": bedrock_region})
                completion_args.update({"aws_access_key_id": creds["AccessKeyId"]})
                completion_args.update({"aws_secret_access_key": creds["SecretAccessKey"]})
                completion_args.update({"aws_session_token": creds["SessionToken"]})
            else:  # assume_role - use default credential chain (IRSA, instance profile, etc.)
                completion_args.update({"aws_region_name": bedrock_region})

        elif self.provider == SupportedLiteLLMProvider.OpenRouter:
            if self.provider_order:

                def _to_order_list(x):
                    if x is None:
                        return []
                    if isinstance(x, str):
                        return [s.strip() for s in x.split(",") if s.strip()]
                    if isinstance(x, (list, tuple)):
                        return [str(s).strip() for s in x if str(s).strip()]
                    return []

                extra_body = {}
                provider_cfg = {}
                provider_order = _to_order_list(self.provider_order)
                provider_cfg["order"] = provider_order
                provider_cfg["allow_fallbacks"] = False
                extra_body["provider"] = provider_cfg
                completion_args.update({"extra_body": extra_body})
        elif self.provider == SupportedLiteLLMProvider.GPUStack:
            completion_args.update(
                {
                    "api_base": urljoin(self.base_url, "v1"),
                }
            )
        elif self.provider == SupportedLiteLLMProvider.Azure_OpenAI:
            completion_args.pop("api_key", None)
            completion_args.pop("api_base", None)
            completion_args.update(
                {
                    "api_key": self.api_key,
                    "api_base": self.base_url,
                    "api_version": self.api_version,
                }
            )

        # Ollama deployments commonly sit behind a reverse proxy that enforces
        # Bearer auth. Ensure the Authorization header is set when an API key
        # is provided, while respecting any user-supplied headers. #11350
        extra_headers = deepcopy(completion_args.get("extra_headers") or {})
        if self.provider == SupportedLiteLLMProvider.Ollama and self.api_key and "Authorization" not in extra_headers:
            extra_headers["Authorization"] = f"Bearer {self.api_key}"
        if extra_headers:
            completion_args["extra_headers"] = extra_headers
        return completion_args