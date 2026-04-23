def get_secret_value(
        self, context: RequestContext, request: GetSecretValueRequest
    ) -> GetSecretValueResponse:
        secret_id = request.get("SecretId")
        version_id = request.get("VersionId")
        version_stage = request.get("VersionStage")
        if not version_id and not version_stage:
            version_stage = "AWSCURRENT"
        self._raise_if_invalid_secret_id(secret_id)
        backend = SecretsmanagerProvider.get_moto_backend_for_resource(secret_id, context)
        self._raise_if_default_kms_key(secret_id, context, backend)
        try:
            response = backend.get_secret_value(secret_id, version_id, version_stage)
            response = decode_secret_binary_from_response(response)
        except moto_exception.SecretNotFoundException:
            raise ResourceNotFoundException(
                f"Secrets Manager can't find the specified secret value for staging label: {version_stage}"
            )
        except moto_exception.ResourceNotFoundException:
            error_message = (
                f"VersionId: {version_id}" if version_id else f"staging label: {version_stage}"
            )
            raise ResourceNotFoundException(
                f"Secrets Manager can't find the specified secret value for {error_message}"
            )
        except moto_exception.SecretStageVersionMismatchException:
            raise InvalidRequestException(
                "You provided a VersionStage that is not associated to the provided VersionId."
            )
        except moto_exception.SecretHasNoValueException:
            raise ResourceNotFoundException(
                f"Secrets Manager can't find the specified secret value for staging label: {version_stage}"
            )
        except moto_exception.InvalidRequestException:
            raise InvalidRequestException(
                "You can't perform this operation on the secret because it was marked for deletion."
            )
        return GetSecretValueResponse(**response)