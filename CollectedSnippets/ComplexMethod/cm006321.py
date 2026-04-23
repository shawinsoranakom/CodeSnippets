async def verify_credentials(
        self,
        *,
        user_id: IdLike,  # noqa: ARG002
        payload: VerifyCredentials,
    ) -> VerifyCredentialsResult:
        """Verify WXO credentials for the target instance.

        Obtains an IAM/MCSP token, then calls the wxO models listing API for the
        configured instance URL. Token-only checks are insufficient because a
        valid API key may authenticate while still lacking access to the tenant
        represented by the instance URL.
        """
        verify_slot = self.payload_schemas.verify_credentials
        if verify_slot is None:
            msg = "Required slot 'verify_credentials' is not configured."
            raise DeploymentError(message=msg, error_code="deployment_error")

        provider_creds = verify_slot.parse(payload.provider_data)

        malformed_credentials_msg = (
            "Provider credentials are malformed. Please ensure the URL and API key are correctly formatted."
        )

        try:
            authenticator = get_authenticator(
                instance_url=payload.base_url,
                api_key=provider_creds.api_key,
            )
        except ValueError as exc:
            raise InvalidContentError(
                message=malformed_credentials_msg,
                cause=exc,
            ) from exc
        except AuthSchemeError:
            raise
        except Exception as exc:
            raise DeploymentError(
                message="Credential verification failed unexpectedly.",
                error_code="deployment_error",
                cause=exc,
            ) from exc

        try:
            await asyncio.to_thread(authenticator.token_manager.get_token)
        except ApiException as exc:
            # Log only the status code for diagnostics and avoid exposing
            # provider response details that could include sensitive values.
            logger.error(  # noqa: TRY400
                "Credential verification failed (status=%s)",
                exc.status_code,
            )
            raise_deployment_error_from_status(
                status_code=exc.status_code,
                detail="Credential verification failed.",
                message_prefix="Credential verification",
                cause=None,
            )
        except Exception as exc:
            raise DeploymentError(
                message="Credential verification failed unexpectedly.",
                error_code="deployment_error",
                cause=exc,
            ) from exc

        def _probe_instance_models() -> None:
            wxo_client = WxOClient(instance_url=payload.base_url, authenticator=authenticator)
            fetch_models_adapter(wxo_client)

        try:
            await asyncio.to_thread(_probe_instance_models)
        except ClientAPIException as exc:
            status_code = exc.response.status_code if exc.response is not None else None
            logger.error(  # noqa: TRY400
                "Credential verification failed: wxO instance probe rejected request (status=%s)",
                status_code,
            )
            raise_deployment_error_from_status(
                status_code=status_code,
                detail="Credential verification failed.",
                message_prefix="Credential verification",
                cause=None,
            )
        except Exception as exc:
            raise DeploymentError(
                message="Credential verification failed unexpectedly.",
                error_code="deployment_error",
                cause=exc,
            ) from exc

        return VerifyCredentialsResult()