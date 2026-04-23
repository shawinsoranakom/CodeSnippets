def serialize_item(item: Any) -> dict[str, Any]:
            if isinstance(item, (TextContent, ImageContent, AudioContent)):
                dumped = item.model_dump()
                # Remove the 'meta' field if it exists and is None (for backward compatibility)
                if dumped.get("meta") is None:
                    dumped.pop("meta", None)
                return dumped
            elif isinstance(item, EmbeddedResource):
                type = item.type
                resource = {}
                for key, val in item.resource.model_dump().items():
                    # Skip 'meta' field if it's None (for backward compatibility)
                    if key == "meta" and val is None:
                        continue
                    if isinstance(val, AnyUrl):
                        resource[key] = str(val)
                    else:
                        resource[key] = val
                dumped_annotations = item.annotations.model_dump() if item.annotations else None
                # Remove 'meta' from annotations if it exists and is None
                if dumped_annotations and dumped_annotations.get("meta") is None:
                    dumped_annotations.pop("meta", None)
                return {"type": type, "resource": resource, "annotations": dumped_annotations}
            elif isinstance(item, ResourceLink):
                dumped = item.model_dump()
                # Remove the 'meta' field if it exists and is None (for backward compatibility)
                if dumped.get("meta") is None:
                    dumped.pop("meta", None)
                # Convert AnyUrl to string for JSON serialization
                if "uri" in dumped and isinstance(dumped["uri"], AnyUrl):
                    dumped["uri"] = str(dumped["uri"])
                return dumped
            else:
                return {}