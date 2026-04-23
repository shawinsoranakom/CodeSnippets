async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle a flow initiated by the user."""
        errors: dict[str, str] = {}

        if user_input is not None:
            normalized_prefix = user_input.get(CONF_PREFIX, "").strip("/")
            # Check for existing entries, treating missing prefix as empty
            for entry in self._async_current_entries(include_ignore=False):
                entry_prefix = (entry.data.get(CONF_PREFIX) or "").strip("/")
                if (
                    entry.data.get(CONF_BUCKET) == user_input[CONF_BUCKET]
                    and entry.data.get(CONF_ENDPOINT_URL)
                    == user_input[CONF_ENDPOINT_URL]
                    and entry_prefix == normalized_prefix
                ):
                    return self.async_abort(reason="already_configured")

            hostname = urlparse(user_input[CONF_ENDPOINT_URL]).hostname
            if not hostname or not hostname.endswith(AWS_DOMAIN):
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
                except ConnectionError:
                    errors[CONF_ENDPOINT_URL] = "cannot_connect"
                else:
                    data = dict(user_input)
                    if not normalized_prefix:
                        # Do not persist empty optional values
                        data.pop(CONF_PREFIX, None)
                    else:
                        data[CONF_PREFIX] = normalized_prefix

                    title = user_input[CONF_BUCKET]
                    if normalized_prefix:
                        title = f"{title} - {normalized_prefix}"

                    return self.async_create_entry(title=title, data=data)

        return self.async_show_form(
            step_id="user",
            data_schema=self.add_suggested_values_to_schema(
                STEP_USER_DATA_SCHEMA, user_input
            ),
            errors=errors,
            description_placeholders={
                "aws_s3_docs_url": DESCRIPTION_AWS_S3_DOCS_URL,
                "boto3_docs_url": DESCRIPTION_BOTO3_DOCS_URL,
            },
        )