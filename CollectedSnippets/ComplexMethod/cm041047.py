def resolve_type_of_property(self, property_def: dict) -> str:
        if property_ref := property_def.get("$ref"):
            ref_definition = self.get_ref_definition(property_ref)
            ref_type = ref_definition.get("type")
            if ref_type not in ["object", "array"]:
                # in this case we simply flatten it (instead of for example creating a type alias)
                resolved_type = TYPE_MAP.get(ref_type)
                if resolved_type is None:
                    LOG.warning(
                        "Type for %s not found in the TYPE_MAP. Using `Any` as fallback.", ref_type
                    )
                    resolved_type = "Any"
            else:
                if ref_type == "object":
                    # the object might only have a pattern defined and no actual properties
                    if "properties" not in ref_definition:
                        resolved_type = "dict"
                    else:
                        nested_struct = self.ref_to_struct(property_ref)
                        resolved_type = nested_struct.name
                        self._add_struct(nested_struct)
                elif ref_type == "array":
                    item_def = ref_definition["items"]
                    item_type = self.resolve_type_of_property(item_def)
                    resolved_type = f"list[{item_type}]"
                else:
                    raise Exception(f"Unknown property type encountered: {ref_type}")
        else:
            match property_type := property_def.get("type"):
                # primitives
                case "string":
                    resolved_type = "str"
                case "boolean":
                    resolved_type = "bool"
                case "integer":
                    resolved_type = "int"
                case "number":
                    resolved_type = "float"
                # complex objects
                case "object":
                    resolved_type = "dict"  # TODO: any cases where we need to continue here?
                case "array":
                    try:
                        item_type = self.resolve_type_of_property(property_def["items"])
                        resolved_type = f"list[{item_type}]"
                    except RecursionError:
                        resolved_type = "list[Any]"
                case _:
                    # TODO: allOf, anyOf, patternProperties (?)
                    # AWS::ApiGateway::RestApi passes a ["object", "string"] here for the "Body" property
                    # it probably makes sense to assume this behaves the same as a "oneOf"
                    if one_of := property_def.get("oneOf"):
                        resolved_type = "|".join([self.resolve_type_of_property(o) for o in one_of])
                    elif isinstance(property_type, list):
                        resolved_type = "|".join([TYPE_MAP[pt] for pt in property_type])
                    else:
                        raise Exception(f"Unknown property type: {property_type}")
        return resolved_type