def _validate_schema(
        schema: dict,
        html_content: str,
        schema_type: str = "CSS",
        expected_fields: Optional[List[str]] = None,
    ) -> dict:
        """Run the generated schema against HTML and return a diagnostic result.

        Args:
            schema: The extraction schema to validate.
            html_content: The HTML to validate against.
            schema_type: "CSS" or "XPATH".
            expected_fields: When provided, enables strict mode — success
                requires ALL expected fields to be present and populated.
                When None, uses fuzzy mode (populated_fields > 0).

        Returns a dict with keys: success, base_elements_found, total_fields,
        populated_fields, field_coverage, field_details, issues,
        sample_base_html, top_level_structure.
        """
        result = {
            "success": False,
            "base_elements_found": 0,
            "total_fields": 0,
            "populated_fields": 0,
            "field_coverage": 0.0,
            "field_details": [],
            "issues": [],
            "sample_base_html": "",
            "top_level_structure": "",
        }

        try:
            StrategyClass = (
                JsonCssExtractionStrategy
                if schema_type.upper() == "CSS"
                else JsonXPathExtractionStrategy
            )
            strategy = StrategyClass(schema=schema)
            items = strategy.extract(url="", html_content=html_content)
        except Exception as e:
            result["issues"].append(f"Extraction crashed: {e}")
            return result

        # Count base elements directly
        try:
            parsed = strategy._parse_html(html_content)
            base_elements = strategy._get_base_elements(parsed, schema["baseSelector"])
            result["base_elements_found"] = len(base_elements)

            # Grab sample innerHTML of first base element (truncated)
            if base_elements:
                sample = strategy._get_element_html(base_elements[0])
                result["sample_base_html"] = sample[:2000]
        except Exception:
            pass

        if result["base_elements_found"] == 0:
            result["issues"].append(
                f"baseSelector '{schema.get('baseSelector', '')}' matched 0 elements"
            )
            result["top_level_structure"] = _get_top_level_structure(html_content)
            return result

        # Analyze field coverage
        all_fields = schema.get("fields", [])
        field_names = [f["name"] for f in all_fields]
        result["total_fields"] = len(field_names)

        for fname in field_names:
            values = [item.get(fname) for item in items]
            populated_count = sum(1 for v in values if v is not None and v != "")
            sample_val = next((v for v in values if v is not None and v != ""), None)
            if sample_val is not None:
                sample_val = str(sample_val)[:120]
            result["field_details"].append({
                "name": fname,
                "populated_count": populated_count,
                "total_count": len(items),
                "sample_value": sample_val,
            })

        result["populated_fields"] = sum(
            1 for fd in result["field_details"] if fd["populated_count"] > 0
        )
        if result["total_fields"] > 0:
            result["field_coverage"] = result["populated_fields"] / result["total_fields"]

        # Build issues
        if result["populated_fields"] == 0:
            result["issues"].append(
                "All fields returned None/empty — selectors likely wrong"
            )
        else:
            empty_fields = [
                fd["name"]
                for fd in result["field_details"]
                if fd["populated_count"] == 0
            ]
            if empty_fields:
                result["issues"].append(
                    f"Fields always empty: {', '.join(empty_fields)}"
                )

        # Check for missing expected fields (strict mode)
        if expected_fields:
            schema_field_names = {f["name"] for f in schema.get("fields", [])}
            missing = [f for f in expected_fields if f not in schema_field_names]
            if missing:
                result["issues"].append(
                    f"Expected fields missing from schema: {', '.join(missing)}"
                )

        # Success criteria
        if expected_fields:
            # Strict: all expected fields must exist in schema AND be populated
            schema_field_names = {f["name"] for f in schema.get("fields", [])}
            populated_names = {
                fd["name"] for fd in result["field_details"] if fd["populated_count"] > 0
            }
            result["success"] = (
                result["base_elements_found"] > 0
                and all(f in populated_names for f in expected_fields)
            )
        else:
            # Fuzzy: at least something extracted
            result["success"] = (
                result["base_elements_found"] > 0 and result["populated_fields"] > 0
            )
        return result