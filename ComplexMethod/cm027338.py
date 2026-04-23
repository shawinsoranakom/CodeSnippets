async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle a flow initiated by the user."""
        errors: dict[str, str] = {}

        if user_input is not None:
            self._async_abort_entries_match(
                {
                    CONF_BUCKET: user_input[CONF_BUCKET],
                    CONF_ENDPOINT_URL: user_input[CONF_ENDPOINT_URL],
                }
            )

            parsed = urlparse(user_input[CONF_ENDPOINT_URL])
            if not parsed.hostname or not parsed.hostname.endswith(
                CLOUDFLARE_R2_DOMAIN
            ):
                errors[CONF_ENDPOINT_URL] = "invalid_endpoint_url"
            else:
                try:
                    session = AioSession()
                    async with session.create_client(
                        "s3",
                        endpoint_url=user_input.get(CONF_ENDPOINT_URL),
                        aws_secret_access_key=user_input[CONF_SECRET_ACCESS_KEY],
                        aws_access_key_id=user_input[CONF_ACCESS_KEY_ID],
                    ) as client:
                        await client.head_bucket(Bucket=user_input[CONF_BUCKET])
                except ClientError:
                    errors["base"] = "invalid_credentials"
                except ParamValidationError as err:
                    if "Invalid bucket name" in str(err):
                        errors[CONF_BUCKET] = "invalid_bucket_name"
                except ValueError:
                    errors[CONF_ENDPOINT_URL] = "invalid_endpoint_url"
                except EndpointConnectionError:
                    errors[CONF_ENDPOINT_URL] = "cannot_connect"
                except ConnectionError:
                    errors[CONF_ENDPOINT_URL] = "cannot_connect"
                else:
                    # Do not persist empty optional values
                    data = dict(user_input)
                    if not data.get(CONF_PREFIX):
                        data.pop(CONF_PREFIX, None)
                    return self.async_create_entry(
                        title=user_input[CONF_BUCKET], data=data
                    )

        return self.async_show_form(
            step_id="user",
            data_schema=self.add_suggested_values_to_schema(
                STEP_USER_DATA_SCHEMA, user_input
            ),
            errors=errors,
            description_placeholders={
                "auth_docs_url": DESCRIPTION_R2_AUTH_DOCS_URL,
            },
        )