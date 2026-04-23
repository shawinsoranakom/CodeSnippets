async def async_step_domain_registration(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle domain registration for all regions."""

        assert self.apis
        assert self.apis[0].private_key
        assert self.domain

        errors: dict[str, str] = {}
        description_placeholders = {
            "public_key_url": f"https://{self.domain}/.well-known/appspecific/com.tesla.3p.public-key.pem",
            "pem": self.apis[0].public_pem,
        }

        successful_response: dict[str, Any] | None = None
        failed_regions: list[str] = []

        for api in self.apis:
            try:
                register_response = await api.partner.register(self.domain)
            except PreconditionFailed:
                return await self.async_step_domain_input(
                    errors={CONF_DOMAIN: "precondition_failed"}
                )
            except TeslaFleetError as e:
                LOGGER.warning(
                    "Partner registration failed for %s: %s",
                    api.server,
                    e.message,
                )
                failed_regions.append(api.server or "unknown")
            else:
                if successful_response is None:
                    successful_response = register_response

        if successful_response is None:
            errors["base"] = "invalid_response"
            return self.async_show_form(
                step_id="domain_registration",
                description_placeholders=description_placeholders,
                errors=errors,
            )

        if failed_regions:
            LOGGER.warning(
                "Partner registration succeeded on some regions but failed on: %s",
                ", ".join(failed_regions),
            )

        # Verify public key from the successful response
        registered_public_key = successful_response.get("response", {}).get(
            "public_key"
        )

        if not registered_public_key:
            errors["base"] = "public_key_not_found"
        elif (
            registered_public_key.lower()
            != self.apis[0].public_uncompressed_point.lower()
        ):
            errors["base"] = "public_key_mismatch"
        else:
            return await self.async_step_registration_complete()

        return self.async_show_form(
            step_id="domain_registration",
            description_placeholders=description_placeholders,
            errors=errors,
        )