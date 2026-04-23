def _serialize_data(data: Any) -> bytes:
                if stream_item_field:
                    value, errors_ = stream_item_field.validate(
                        data, {}, loc=("response",)
                    )
                    if errors_:
                        ctx = endpoint_ctx or EndpointContext()
                        raise ResponseValidationError(
                            errors=errors_,
                            body=data,
                            endpoint_ctx=ctx,
                        )
                    return stream_item_field.serialize_json(
                        value,
                        include=response_model_include,
                        exclude=response_model_exclude,
                        by_alias=response_model_by_alias,
                        exclude_unset=response_model_exclude_unset,
                        exclude_defaults=response_model_exclude_defaults,
                        exclude_none=response_model_exclude_none,
                    )
                else:
                    data = jsonable_encoder(data)
                    return json.dumps(data).encode("utf-8")