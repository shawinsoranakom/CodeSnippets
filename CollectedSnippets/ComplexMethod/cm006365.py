async def get_webhook_user(self, flow_id: str, request: Request) -> UserRead:
        settings_service = self.settings

        if not settings_service.auth_settings.WEBHOOK_AUTH_ENABLE:
            try:
                flow_owner = await get_user_by_flow_id_or_endpoint_name(flow_id)
                if flow_owner is None:
                    raise HTTPException(status_code=404, detail="Flow not found")
                return flow_owner  # noqa: TRY300
            except HTTPException:
                raise
            except Exception as exc:
                raise HTTPException(status_code=404, detail="Flow not found") from exc

        api_key_header_val = request.headers.get("x-api-key")
        api_key_query_val = request.query_params.get("x-api-key")

        if not api_key_header_val and not api_key_query_val:
            raise HTTPException(status_code=403, detail="API key required when webhook authentication is enabled")

        api_key = api_key_header_val or api_key_query_val

        try:
            async with session_scope() as db:
                result = await check_key(db, api_key)
                if not result:
                    logger.warning("Invalid API key provided for webhook")
                    raise HTTPException(status_code=403, detail="Invalid API key")

                authenticated_user = UserRead.model_validate(result, from_attributes=True)
                logger.info("Webhook API key validated successfully")
        except HTTPException:
            raise
        except Exception as exc:
            logger.error(f"Webhook API key validation error: {exc}")
            raise HTTPException(status_code=403, detail="API key authentication failed") from exc

        try:
            flow_owner = await get_user_by_flow_id_or_endpoint_name(flow_id)
            if flow_owner is None:
                raise HTTPException(status_code=404, detail="Flow not found")
        except HTTPException:
            raise
        except Exception as exc:
            raise HTTPException(status_code=404, detail="Flow not found") from exc

        if flow_owner.id != authenticated_user.id:
            raise HTTPException(
                status_code=403,
                detail="Access denied: You can only execute webhooks for flows you own",
            )

        return authenticated_user