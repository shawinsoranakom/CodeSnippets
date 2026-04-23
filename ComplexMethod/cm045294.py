def stringify_attributes(
                    attributes: Mapping[str, cloudevent_pb2.CloudEvent.CloudEventAttributeValue],
                ) -> Mapping[str, str]:
                    result: Dict[str, str] = {}
                    for key, value in attributes.items():
                        item = None
                        match value.WhichOneof("attr"):
                            case "ce_boolean":
                                item = str(value.ce_boolean)
                            case "ce_integer":
                                item = str(value.ce_integer)
                            case "ce_string":
                                item = value.ce_string
                            case "ce_bytes":
                                item = str(value.ce_bytes)
                            case "ce_uri":
                                item = value.ce_uri
                            case "ce_uri_ref":
                                item = value.ce_uri_ref
                            case "ce_timestamp":
                                item = str(value.ce_timestamp)
                            case _:
                                raise ValueError("Unknown attribute kind")
                        result[key] = item

                    return result