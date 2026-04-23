def data_schema_to_columns_defs(  # noqa: PLR0912
    openapi_json,
    operation_id,
    provider,
    route: str | None = None,
    get_widget_config: bool = False,
):
    """Convert data schema to column definitions for the widget."""
    schema_refs: list = []
    result_schema_ref = get_data_schema_for_widget(openapi_json, operation_id, route)

    # Check if 'anyOf' is in the result_schema_ref and handle the nested structure
    if result_schema_ref and "anyOf" in result_schema_ref:
        for item in result_schema_ref["anyOf"]:
            # When there are multiple providers a 'oneOf' is used
            if "items" in item and "oneOf" in item["items"]:
                # Extract the $ref values
                schema_refs.extend(
                    [
                        oneOf_item["$ref"].split("/")[-1]
                        for oneOf_item in item["items"]["oneOf"]
                        if "$ref" in oneOf_item
                    ]
                )
            # When there's only one model there is no oneOf
            elif "items" in item and "$ref" in item["items"]:
                schema_refs.append(item["items"]["$ref"].split("/")[-1])
            elif "$ref" in item:
                schema_refs.append(item["$ref"].split("/")[-1])
            elif "oneOf" in item:
                for ref in item.get("oneOf", []):
                    maybe_ref = ref.get("$ref").split("/")[-1]
                    if maybe_ref.lower().startswith(provider):
                        schema_refs.append(maybe_ref)
                        break

    # Fetch the schemas using the extracted references
    schemas = [
        openapi_json["components"]["schemas"][ref]
        for ref in schema_refs
        if ref and ref in openapi_json["components"]["schemas"]
    ]

    if not schemas and result_schema_ref and "properties" in result_schema_ref:
        schemas.append(result_schema_ref)

    # Proceed with finding common keys and generating column definitions
    if not schemas:
        return []

    target_schema: dict = {}

    if len(schemas) == 1:
        target_schema = schemas[0]
    else:
        for schema in schemas:
            schema_desc = schema.get("description", "").lower()
            provider_lower = provider.lower().replace("tradingeconomics", "te")
            # Check if description starts with provider name (with or without underscores/spaces)
            provider_variants = [
                provider_lower,
                provider_lower.replace("_", " "),
                provider_lower.replace("_", ""),
            ]
            if any(schema_desc.startswith(v) for v in provider_variants) or (
                schema_desc.startswith("us government")
            ):
                target_schema = schema
                break
        # Fallback: if no description match, try matching by schema title/name
        if not target_schema:
            for schema in schemas:
                schema_title = schema.get("title", "").lower()
                if provider.lower().replace("_", "") in schema_title.replace("_", ""):
                    target_schema = schema
                    break
        # Final fallback: use the first schema if still no match
        if not target_schema and schemas:
            target_schema = schemas[0]

    if get_widget_config:
        return target_schema.get("x-widget_config", {})

    keys = list(target_schema.get("properties", {}))
    column_defs: list = []

    for key in keys:
        cell_data_type = None
        formatterFn = None
        prop = target_schema.get("properties", {}).get(key)

        # Handle prop types for both when there's a single prop type or multiple
        if "items" in prop:
            items = prop.get("items", {})
            items = items.get("anyOf", items)
            prop["anyOf"] = items if isinstance(items, list) else [items]
            types = [
                sub_prop.get("type") for sub_prop in prop["anyOf"] if "type" in sub_prop
            ]
            if "number" in types or "integer" in types or "float" in types:
                cell_data_type = "number"
            elif "string" in types and any(
                sub_prop.get("format") in ["date", "date-time"]
                for sub_prop in prop["anyOf"]
                if "format" in sub_prop
            ):
                cell_data_type = "date"
            else:
                cell_data_type = "text"
        elif "anyOf" in prop:
            types = [
                sub_prop.get("type") for sub_prop in prop["anyOf"] if "type" in sub_prop
            ]
            if "number" in types or "integer" in types or "float" in types:
                cell_data_type = "number"
            elif "string" in types and any(
                sub_prop.get("format") in ["date", "date-time"]
                for sub_prop in prop["anyOf"]
                if "format" in sub_prop
            ):
                cell_data_type = "date"
            else:
                cell_data_type = "text"
        else:
            prop_type = prop.get("type", None)
            if prop_type in ["number", "integer", "float"]:
                cell_data_type = "number"
                if prop_type == "integer":
                    formatterFn = "int"
            elif "format" in prop and prop["format"] in ["date", "date-time"]:
                cell_data_type = "date"
            else:
                cell_data_type = "text"

        column_def: dict = {}
        # OpenAPI changes some of the field names.
        k = to_snake_case(key)
        column_def["field"] = k

        if k in [
            "date",
            "symbol",
        ]:
            column_def["pinned"] = "left"

        column_def["formatterFn"] = formatterFn
        header_name = prop.get("title", key.title())
        column_def["headerName"] = " ".join(
            [
                (word.upper() if word in TO_CAPS_STRINGS else word)
                for word in header_name.replace("_", " ").split(" ")
            ]
        )
        column_def["headerTooltip"] = prop.get(
            "description", prop.get("title", key.title())
        )
        column_def["cellDataType"] = cell_data_type
        measurement = prop.get("x-unit_measurement")

        if measurement == "percent":
            column_def["formatterFn"] = (
                "normalizedPercent"
                if prop.get("x-frontend_multiply") == 100
                else "percent"
            )
            column_def["renderFn"] = "greenRed"
            column_def["cellDataType"] = "number"

        if k in [
            "cik",
            "isin",
            "figi",
            "cusip",
            "sedol",
            "symbol",
            "children",
            "element_id",
            "parent_id",
        ]:
            column_def["cellDataType"] = "text"
            column_def["formatterFn"] = "none"
            column_def["renderFn"] = None

            if k not in ["symbol", "children", "element_id", "parent_id"]:
                column_def["headerName"] = column_def["headerName"].upper()

        if k in ["fiscal_year", "year", "year_born", "calendar_year"]:
            column_def["cellDataType"] = "number"
            column_def["formatterFn"] = "none"

        if (
            route
            and route.endswith("chains")
            and column_def.get("field")
            in [
                "underlying_symbol",
                "contract_symbol",
                "underlying_price",
                "contract_symbol",
            ]
        ):
            column_def["hide"] = True

        if column_def.get("field") in [
            "delta",
            "gamma",
            "theta",
            "vega",
            "rho",
            "vega",
            "charm",
            "vanna",
            "vomma",
        ]:
            column_def["formatterFn"] = "none"
            if column_def["field"] in ["delta", "theta", "rho"]:
                column_def["renderFn"] = "greenRed"

        if (
            route
            and route.endswith("chains")
            and column_def["field"] == "implied_volatility"
        ):
            column_def["formatterFn"] = "normalizedPercent"

        if column_def.get("field") == "change":
            column_def["renderFn"] = "greenRed"

        if (
            route
            and route.endswith("chains")
            and column_def.get("field")
            in [
                "underlying_symbol",
                "contract_symbol",
                "underlying_price",
                "contract_symbol",
            ]
        ):
            column_def["hide"] = True

        if column_def.get("field") in [
            "delta",
            "gamma",
            "theta",
            "vega",
            "rho",
            "vega",
            "charm",
            "vanna",
            "vomma",
        ]:
            column_def["formatterFn"] = "none"
            if column_def["field"] in ["delta", "theta", "rho"]:
                column_def["renderFn"] = "greenRed"

        if (
            route
            and route.endswith("chains")
            and column_def["field"] == "implied_volatility"
        ):
            column_def["formatterFn"] = "normalizedPercent"

        if column_def.get("field") == "change":
            column_def["renderFn"] = "greenRed"

        # Check for x-widget_config in property definition
        if _widget_config := prop.get("x-widget_config", {}):
            if _widget_config.get("exclude"):
                continue

            column_def.update(_widget_config)

        # Also check for x-widget_config at schema root level (from model_config.json_schema_extra)
        schema_level_field = target_schema.get(key, {})

        if isinstance(schema_level_field, dict) and (
            schema_level_config := schema_level_field.get("x-widget_config", {})
        ):
            if schema_level_config.get("exclude"):
                continue

            column_def.update(schema_level_config)

        column_defs.append(column_def)

    return column_defs