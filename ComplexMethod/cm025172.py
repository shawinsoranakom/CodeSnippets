async def async_finish_flow(
        self,
        flow: FlowHandler[AuthFlowContext, AuthFlowResult, tuple[str, str]],
        result: AuthFlowResult,
    ) -> AuthFlowResult:
        """Return a user as result of login flow.

        This method is called when a flow step returns FlowResultType.ABORT or
        FlowResultType.CREATE_ENTRY.
        """
        flow = cast(LoginFlow, flow)

        if result["type"] != FlowResultType.CREATE_ENTRY:
            return result

        # we got final result
        if isinstance(result["data"], models.Credentials):
            result["result"] = result["data"]
            return result

        auth_provider = self.auth_manager.get_auth_provider(*result["handler"])
        if not auth_provider:
            raise KeyError(f"Unknown auth provider {result['handler']}")

        credentials = await auth_provider.async_get_or_create_credentials(
            cast(Mapping[str, str], result["data"]),
        )

        if flow.context.get("credential_only"):
            result["result"] = credentials
            return result

        # multi-factor module cannot enabled for new credential
        # which has not linked to a user yet
        if auth_provider.support_mfa and not credentials.is_new:
            user = await self.auth_manager.async_get_user_by_credentials(credentials)
            if user is not None:
                modules = await self.auth_manager.async_get_enabled_mfa(user)

                if modules:
                    flow.credential = credentials
                    flow.user = user
                    flow.available_mfa_modules = modules
                    return await flow.async_step_select_mfa_module()

        result["result"] = credentials
        return result