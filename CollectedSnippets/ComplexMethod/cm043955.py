def fetch_data(
        self,
        dataflow: str,
        start_date: str | None = None,
        end_date: str | None = None,
        limit: int | None = None,
        _skip_validation: bool = False,
        **kwargs,
    ) -> dict:
        """Fetch data from the IMF API for a given dataflow and parameters.

        Uses XML format for data retrieval as the JSON format has data truncation issues.

        Parameters
        ----------
        dataflow : str
            The dataflow ID
        start_date : str | None
            Start date for the query
        end_date : str | None
            End date for the query
        _skip_validation : bool
            If True, skip constraint validation (use when caller already validated)
        **kwargs
            Dimension parameters
        """
        # pylint: disable=import-outside-toplevel
        from openbb_core.app.model.abstract.error import OpenBBError
        from openbb_core.provider.utils.errors import EmptyDataError
        from openbb_core.provider.utils.helpers import make_request
        from openbb_imf.utils.helpers import parse_time_period
        from openbb_imf.utils.table_presentation import (
            extract_unit_from_label,
            parse_unit_and_scale,
        )
        from pandas import DataFrame, to_numeric
        from requests.exceptions import RequestException

        # Validate dimension constraints before making the API call
        if not _skip_validation:
            self.validate_dimension_constraints(
                dataflow, start_date=start_date, end_date=end_date, **kwargs
            )

        url = self.build_url(dataflow, start_date, end_date, limit=limit, **kwargs)
        headers = {
            "Accept": "application/xml",
            "Cache-Control": "no-cache",
            "User-Agent": "Open Data Platform - IMF Data Fetcher",
        }
        response = None

        try:
            response = make_request(url, headers=headers)
            response.raise_for_status()
            xml_content = response.text
        except RequestException as e:
            res_content = response.text if response else ""
            raise OpenBBError(
                f"An error occurred during the HTTP request: {url} -> {e} -> {res_content}"
            ) from e

        # Parse XML
        try:
            import defusedxml.ElementTree as DefusedET

            root = DefusedET.fromstring(xml_content)
        except Exception as e:  # pylint: disable=broad-except
            raise OpenBBError(f"Failed to parse XML response: {url} -> {e}") from e

        # Define namespaces used in IMF SDMX responses
        namespaces = {
            "message": "http://www.sdmx.org/resources/sdmxml/schemas/v3_0/message",
            "ss": "http://www.sdmx.org/resources/sdmxml/schemas/v3_0/data/structurespecific",
            "common": "http://www.sdmx.org/resources/sdmxml/schemas/v3_0/common",
        }

        # Find all Series elements
        dataset = root.find(".//message:DataSet", namespaces)
        if dataset is None:
            # Try without namespace prefix
            dataset = root.find(".//DataSet")
        if dataset is None:
            # Try with ss namespace
            dataset = root.find(".//ss:DataSet", namespaces)
        if dataset is None:
            raise OpenBBError(
                EmptyDataError(f"No data found in the response. URL: {url}")
            )

        # Parse Group elements to extract group-level attributes (UNIT, ACCOUNTING_ENTRY, etc.)
        # Group structure: <Group INDICATOR="..." ns1:type="GROUP_INDICATOR">
        #                    <Comp id="UNIT"><Value>USD</Value></Comp>
        #                    <Comp id="ACCOUNTING_ENTRY"><Value>NETLA</Value></Comp>
        #                  </Group>
        group_attributes: dict[str, dict[str, str]] = {}

        # Find all Group elements - they can have namespace prefix
        for group in dataset.findall("Group") + dataset.findall("ss:Group", namespaces):
            # The group key is typically the INDICATOR code or similar dimension
            group_key = None
            for attr_name, attr_value in group.attrib.items():
                # Skip namespace type attributes like ns1:type
                if "type" in attr_name.lower() and "group" in attr_value.lower():
                    continue
                # The first non-type attribute is the key (e.g., INDICATOR)
                group_key = attr_value
                break

            if not group_key:
                continue

            # Extract Comp elements containing group-level attribute values
            group_attrs: dict[str, str] = {}
            for comp in group.findall("Comp") + group.findall("ss:Comp", namespaces):
                comp_id = comp.attrib.get("id")
                if comp_id:
                    # Value is in a child <Value> element
                    value_elem = comp.find("Value") or comp.find("ss:Value", namespaces)
                    if value_elem is not None and value_elem.text:
                        group_attrs[comp_id] = value_elem.text

            if group_attrs:
                group_attributes[group_key] = group_attrs

        # Get dataflow metadata
        dataflow_obj = self.metadata.dataflows.get(dataflow, {})
        # Build translation maps for dimension values
        translation_maps = self._get_cached_translations(dataflow)
        # Build dimension order mapping for proper series_id construction
        structure_ref = dataflow_obj.get("structureRef", {})
        dsd_id = structure_ref.get("id")
        indicator_dimension_order: dict[str, int] = {}
        indicator_id_candidates = [
            "INDICATOR",
            "PRODUCTION_INDEX",
            "COICOP_1999",
            "INDEX_TYPE",
            "ACTIVITY",
            "PRODUCT",
            "SERIES",
            "ITEM",
            "BOP_ACCOUNTING_ENTRY",
            "ACCOUNTING_ENTRY",
        ]

        if dsd_id and dsd_id in self.metadata.datastructures:
            dsd = self.metadata.datastructures[dsd_id]
            dimensions = dsd.get("dimensions", [])

            for idx, dim in enumerate(dimensions):
                dim_id = dim.get("id", "")

                if not dim_id:
                    continue

                if dim_id in indicator_id_candidates or any(
                    keyword in dim_id
                    for keyword in ["INDICATOR", "ACCOUNTING_ENTRY", "ENTRY"]
                ):
                    indicator_dimension_order[dim_id] = idx

        # Process all Series elements
        all_data_rows: list = []
        all_unique_indicators: set = set()
        all_series_derivation_types: dict = {}

        # Build dimension order map for consistent title and series_id ordering
        dim_order_map: dict[str, int] = {}
        # Build attribute codelist map for proper code translation
        attr_codelist_map: dict[str, dict] = {}
        if dsd_id and dsd_id in self.metadata.datastructures:
            dsd = self.metadata.datastructures[dsd_id]
            for idx, dim in enumerate(dsd.get("dimensions", [])):
                dim_order_map[dim.get("id", "")] = idx
            # Resolve codelists for attributes (UNIT, SCALE, etc.)
            for attr in dsd.get("attributes", []):
                attr_id = attr.get("id")
                if attr_id:
                    codelist_id = self.metadata._resolve_codelist_id(
                        dataflow, dsd_id, attr_id, attr
                    )
                    if codelist_id and codelist_id in self.metadata._codelist_cache:
                        attr_codelist_map[attr_id] = self.metadata._codelist_cache[
                            codelist_id
                        ]

        # Find Series elements with multiple namespace approaches
        series_elements = dataset.findall("Series") + dataset.findall(
            "ss:Series", namespaces
        )

        # Remove duplicates while preserving order
        seen_series = set()
        unique_series = []
        for s in series_elements:
            s_id = id(s)
            if s_id not in seen_series:
                seen_series.add(s_id)
                unique_series.append(s)
        series_elements = unique_series

        for series in series_elements:
            # Extract series attributes (dimensions)
            series_meta: dict = {}
            indicator_code = None
            indicator_codes_list: list = []
            all_dimension_codes: list = []  # Track ALL dimension codes for series_id
            # Collect ALL dimension labels for building a complete title
            # Format: (position, dimension_id, display_value)
            title_parts: list[tuple[int, str, str]] = []
            # Dimensions to EXCLUDE from title (they have their own columns or are metadata)
            # Note: COUNTERPART_COUNTRY is NOT excluded - it's meaningful for DIP, BOP, etc.
            title_exclude_dims = {
                "COUNTRY",
                "REF_AREA",
                "TIME_PERIOD",
                "SCALE",
                "UNIT",
                "FREQ",
                "FREQUENCY",
                "OBS_VALUE",
                "OBS_STATUS",
            }

            for attr_name, attr_value in series.attrib.items():
                # Track ALL dimension codes for complete series_id
                all_dimension_codes.append((attr_name, attr_value))

                # Special handling for indicator-like dimensions
                if attr_name in indicator_id_candidates or "INDICATOR" in attr_name:
                    indicator_code = attr_value
                    indicator_codes_list.append((attr_name, attr_value))
                    all_unique_indicators.add(attr_value)

                    # Translate the code to human-readable label
                    if (
                        attr_name in translation_maps
                        and attr_value in translation_maps[attr_name]
                    ):
                        display_value = translation_maps[attr_name][attr_value]
                    else:
                        display_value = attr_value

                    series_meta[attr_name] = display_value
                    series_meta[f"{attr_name}_code"] = attr_value
                    # Add to title parts with high position (indicator goes last)
                    dim_pos = dim_order_map.get(attr_name, 999)
                    title_parts.append((dim_pos, attr_name, display_value))

                elif attr_name == "COUNTRY":
                    # Translate country code
                    if (
                        attr_name in translation_maps
                        and attr_value in translation_maps[attr_name]
                    ):
                        display_value = translation_maps[attr_name][attr_value]
                    else:
                        display_value = attr_value
                    series_meta[attr_name] = display_value
                    series_meta["country_code"] = attr_value

                elif attr_name == "COUNTERPART_COUNTRY":
                    if (
                        attr_name in translation_maps
                        and attr_value in translation_maps[attr_name]
                    ):
                        display_value = translation_maps[attr_name][attr_value]
                    else:
                        display_value = attr_value
                    series_meta[attr_name] = display_value
                    series_meta["counterpart_country_code"] = attr_value
                    # Add to title parts - COUNTERPART_COUNTRY is meaningful for DIP, BOP
                    dim_pos = dim_order_map.get(attr_name, 999)
                    title_parts.append((dim_pos, attr_name, display_value))

                elif attr_name == "SCALE":
                    # Handle scale/unit multiplier - use proper codelist from DSD
                    try:
                        scale_int = int(attr_value)
                        series_meta["unit_multiplier"] = (
                            1 if scale_int == 0 else 10**scale_int
                        )
                        # Use DSD-specific codelist if available, else CL_UNIT_MULT
                        if attr_name in attr_codelist_map:
                            scale_codelist = attr_codelist_map[attr_name]
                            series_meta["scale"] = scale_codelist.get(
                                attr_value, f"10^{attr_value}"
                            )
                        elif cl_unit_mult := self.metadata._codelist_cache.get(
                            "CL_UNIT_MULT", {}
                        ):
                            series_meta["scale"] = cl_unit_mult.get(
                                attr_value, f"10^{attr_value}"
                            )
                        else:
                            series_meta["scale"] = f"10^{attr_value}"
                    except ValueError:
                        series_meta["scale"] = attr_value

                elif attr_name == "UNIT":
                    # Handle unit - use proper codelist from DSD, not generic CL_UNIT
                    if attr_name in attr_codelist_map:
                        unit_codelist = attr_codelist_map[attr_name]
                        series_meta["unit"] = unit_codelist.get(attr_value, attr_value)
                    else:
                        # Fallback to generic CL_UNIT only if no DSD-specific codelist
                        cl_unit = self.metadata._codelist_cache.get("CL_UNIT", {})
                        series_meta["unit"] = cl_unit.get(attr_value, attr_value)

                elif (
                    attr_name in translation_maps
                    and attr_value in translation_maps[attr_name]
                ):
                    # Store translated label and preserve code
                    display_value = translation_maps[attr_name][attr_value]
                    series_meta[attr_name] = display_value
                    series_meta[f"{attr_name}_code"] = attr_value
                    # Add to title parts if not excluded
                    if attr_name not in title_exclude_dims:
                        dim_pos = dim_order_map.get(attr_name, 999)
                        title_parts.append((dim_pos, attr_name, display_value))
                elif attr_name not in [
                    "IFS_FLAG",
                    "OVERLAP",
                    "OBS_STATUS",
                    "DECIMALS_DISPLAYED",
                    "COUNTRY_UPDATE_DATE",
                ]:
                    # Dimension not in translation maps - store raw value
                    # Also store with _code suffix for consistency
                    series_meta[attr_name] = attr_value
                    series_meta[f"{attr_name}_code"] = attr_value
                    # Add to title parts if not excluded (use raw code as display)
                    if attr_name not in title_exclude_dims:
                        dim_pos = dim_order_map.get(attr_name, 999)
                        title_parts.append((dim_pos, attr_name, attr_value))

            # Store indicator_codes for series_id building
            if indicator_codes_list:
                series_meta["indicator_codes"] = indicator_codes_list

            # Build title from ALL collected dimension labels
            # Sort by DSD dimension position so title is consistent
            if title_parts:
                sorted_title_parts = sorted(title_parts, key=lambda x: (x[0], x[1]))
                series_meta["title"] = " - ".join(p[2] for p in sorted_title_parts)

            # Apply group-level attributes (UNIT, ACCOUNTING_ENTRY, etc.) from Group elements
            # The group_attributes dict maps indicator codes to their group-level attrs
            if indicator_code and indicator_code in group_attributes:
                group_attrs = group_attributes[indicator_code]
                for attr_id, attr_value in group_attrs.items():
                    if attr_id == "UNIT" and "unit" not in series_meta:
                        # Translate UNIT code
                        if "UNIT" in attr_codelist_map:
                            unit_codelist = attr_codelist_map["UNIT"]
                            series_meta["unit"] = unit_codelist.get(
                                attr_value, attr_value
                            )
                        elif cl_unit := self.metadata._codelist_cache.get("CL_UNIT"):
                            series_meta["unit"] = cl_unit.get(attr_value, attr_value)
                        else:
                            series_meta["unit"] = attr_value
                    elif attr_id == "SCALE" and "scale" not in series_meta:
                        try:
                            scale_int = int(attr_value)
                            series_meta["unit_multiplier"] = (
                                1 if scale_int == 0 else 10**scale_int
                            )
                            if "SCALE" in attr_codelist_map:
                                scale_codelist = attr_codelist_map["SCALE"]
                                series_meta["scale"] = scale_codelist.get(
                                    attr_value, f"10^{attr_value}"
                                )
                            elif cl_unit_mult := self.metadata._codelist_cache.get(
                                "CL_UNIT_MULT"
                            ):
                                series_meta["scale"] = cl_unit_mult.get(
                                    attr_value, f"10^{attr_value}"
                                )
                            else:
                                series_meta["scale"] = f"10^{attr_value}"
                        except ValueError:
                            series_meta["scale"] = attr_value
                    elif attr_id not in series_meta:
                        # Translate using translation maps if available
                        if (
                            attr_id in translation_maps
                            and attr_value in translation_maps[attr_id]
                        ):
                            series_meta[attr_id] = translation_maps[attr_id][attr_value]
                            series_meta[f"{attr_id}_code"] = attr_value
                        else:
                            series_meta[attr_id] = attr_value

            if "unit" not in series_meta:
                # Get CL_UNIT codelist for looking up unit codes
                cl_unit = self.metadata._codelist_cache.get("CL_UNIT", {})
                # First check TYPE_OF_TRANSFORMATION which provides unit-like info
                type_of_transform = series_meta.get("TYPE_OF_TRANSFORMATION")
                if type_of_transform:
                    # TYPE_OF_TRANSFORMATION may contain compound values like
                    # "Period average, Year-over-year (YOY) percent change"
                    # Try to extract just the unit part
                    if type_of_transform in ["Index", "Weight", "Ratio"]:
                        series_meta["unit"] = type_of_transform
                    elif "percent change" in type_of_transform.lower():
                        series_meta["unit"] = "Percent change"
                        if "year-over-year" in type_of_transform.lower():
                            series_meta["scale"] = "Year-over-year"
                        elif "period-over-period" in type_of_transform.lower():
                            series_meta["scale"] = "Period-over-period"
                    elif ", " in type_of_transform:
                        # Try last part after comma (e.g., "Weight, Percent" -> "Percent")
                        last_part = type_of_transform.split(", ")[-1].strip()
                        if last_part in ["Index", "Percent", "Weight", "Ratio"]:
                            series_meta["unit"] = last_part
                        else:
                            series_meta["unit"] = type_of_transform
                    else:
                        series_meta["unit"] = type_of_transform

                # Try extracting unit AND scale from indicator label
                # Label format: "Description, Scale, Unit" e.g.,
                # "Exporter real GDP, Per capita, US dollar"
                indicator_label = series_meta.get("INDICATOR")
                extracted_unit = None
                extracted_scale = None
                if indicator_label:
                    extracted_unit_string = extract_unit_from_label(indicator_label)
                    if extracted_unit_string:
                        extracted_unit, extracted_scale = parse_unit_and_scale(
                            extracted_unit_string
                        )

                # If still no unit, try extracting from indicator code suffix
                # e.g., XQI_IX -> IX -> "Index" (from CL_UNIT)
                # BUT: only if the suffix is actually a unit code, not a dimension code
                # like "ALL" (All entities) or country codes
                if "unit" not in series_meta:
                    ind_code = series_meta.get("INDICATOR_code")
                    if ind_code and "_" in ind_code:
                        parts = ind_code.rsplit("_", 1)
                        if len(parts) == 2:
                            unit_code = parts[1]
                            # Skip common dimension codes that appear as suffixes
                            dimension_codes = {"ALL", "FE", "RFI", "REXFI"}
                            if (
                                unit_code in cl_unit
                                and unit_code not in dimension_codes
                            ):
                                series_meta["unit"] = cl_unit[unit_code]

                if extracted_scale:
                    # Only override if current scale is generic or missing
                    current_scale = series_meta.get("scale")
                    generic_scales = {"Units", "units", None, ""}
                    if current_scale in generic_scales or not current_scale:
                        series_meta["scale"] = extracted_scale

                # If still no unit, use extracted unit from label
                if "unit" not in series_meta and extracted_unit:
                    series_meta["unit"] = extracted_unit

                # If still no unit, try other label sources
                if "unit" not in series_meta:
                    # Try these label sources in order of priority
                    label_sources = [
                        series_meta.get("title"),  # May be overwritten by PRODUCT
                        series_meta.get("PRODUCTION_INDEX"),
                        series_meta.get("INDEX_TYPE"),
                    ]
                    for label in label_sources:
                        if label:
                            extracted_unit_string = extract_unit_from_label(label)
                            if extracted_unit_string:
                                # Parse into separate unit and scale components
                                unit, scale = parse_unit_and_scale(
                                    extracted_unit_string
                                )
                                if unit:
                                    series_meta["unit"] = unit
                                if scale and "scale" not in series_meta:
                                    series_meta["scale"] = scale
                                break

            # Match the input format: dataflow::indicator_code
            if indicator_codes_list:
                # Sort by DSD dimension order for consistency
                sorted_ind_codes = sorted(
                    indicator_codes_list,
                    key=lambda x: (indicator_dimension_order.get(x[0], 999), x[0]),
                )
                combined_codes = "_".join(code for _, code in sorted_ind_codes)
                series_meta["series_id"] = f"{dataflow}::{combined_codes}"
            elif indicator_code:
                # Fallback if no indicator codes list
                series_meta["series_id"] = f"{dataflow}::{indicator_code}"

            # Process observations with multiple namespace approaches
            obs_elements = series.findall("Obs") + series.findall("ss:Obs", namespaces)
            # Remove duplicates
            seen_obs = set()
            unique_obs = []
            for o in obs_elements:
                o_id = id(o)
                if o_id not in seen_obs:
                    seen_obs.add(o_id)
                    unique_obs.append(o)

            derivation_types_in_series: set = set()

            for obs in unique_obs:
                obs_row = series_meta.copy()

                # TIME_PERIOD - try multiple attribute names
                time_period = (
                    obs.attrib.get("TIME_PERIOD")
                    or obs.attrib.get("TIME")
                    or obs.attrib.get("time")
                    or ""
                )

                # Get observation value - SDMX 3.0 XML format
                # Value can be in OBS_VALUE attribute or ObsValue child element
                obs_value = obs.attrib.get("OBS_VALUE") or obs.attrib.get("OBSERVATION")

                # If not in attributes, check child elements
                if obs_value is None:
                    # Try ObsValue element with namespace
                    obs_value_elem = obs.find("ss:ObsValue", namespaces)
                    if obs_value_elem is None:
                        obs_value_elem = obs.find("ObsValue")
                    if obs_value_elem is not None:
                        obs_value = (
                            obs_value_elem.attrib.get("value") or obs_value_elem.text
                        )
                    else:
                        # Search all children for value-like elements
                        for child in obs:
                            local_tag = (
                                child.tag.split("}")[-1]
                                if "}" in child.tag
                                else child.tag
                            )
                            if local_tag.upper() in ("OBSVALUE", "OBS_VALUE", "VALUE"):
                                obs_value = child.attrib.get("value") or child.text
                                if obs_value:
                                    break

                derivation_type = obs.attrib.get("DERIVATION_TYPE")
                obs_row["TIME_PERIOD"] = time_period

                # Extract observation-level attributes (UNIT, SCALE, etc.)
                # These may override series-level attributes for specific observations
                obs_unit = obs.attrib.get("UNIT")
                if obs_unit:
                    # Use proper codelist from DSD, not generic CL_UNIT
                    if "UNIT" in attr_codelist_map:
                        unit_codelist = attr_codelist_map["UNIT"]
                        obs_row["unit"] = unit_codelist.get(obs_unit, obs_unit)
                    else:
                        cl_unit = self.metadata._codelist_cache.get("CL_UNIT", {})
                        obs_row["unit"] = cl_unit.get(obs_unit, obs_unit)

                obs_scale = obs.attrib.get("SCALE")
                if obs_scale:
                    try:
                        scale_int = int(obs_scale)
                        obs_row["unit_multiplier"] = (
                            1 if scale_int == 0 else 10**scale_int
                        )
                        # Use DSD-specific codelist if available
                        if "SCALE" in attr_codelist_map:
                            scale_codelist = attr_codelist_map["SCALE"]
                            obs_row["scale"] = scale_codelist.get(
                                obs_scale, f"10^{obs_scale}"
                            )
                        elif cl_unit_mult := self.metadata._codelist_cache.get(
                            "CL_UNIT_MULT", {}
                        ):
                            obs_row["scale"] = cl_unit_mult.get(
                                obs_scale, f"10^{obs_scale}"
                            )
                        else:
                            obs_row["scale"] = f"10^{obs_scale}"
                    except ValueError:
                        obs_row["scale"] = obs_scale

                # Only add rows with actual values
                if obs_value is not None and obs_value not in {"", "D"}:
                    obs_row["value"] = obs_value

                    if derivation_type:
                        if "CL_DERIVATION_TYPE" in self.metadata._codelist_cache:
                            derivation_type = self.metadata._codelist_cache[
                                "CL_DERIVATION_TYPE"
                            ].get(derivation_type, derivation_type)
                        derivation_types_in_series.add(derivation_type)

                    all_data_rows.append(obs_row)

            if indicator_code and derivation_types_in_series:
                if len(derivation_types_in_series) == 1:
                    all_series_derivation_types[indicator_code] = list(
                        derivation_types_in_series
                    )[0]
                else:
                    all_series_derivation_types[indicator_code] = "; ".join(
                        sorted(derivation_types_in_series)
                    )

        if not all_data_rows:
            # Build a more helpful error message with parameter info
            param_info = ", ".join(f"{k}={v}" for k, v in kwargs.items() if v)
            raise OpenBBError(
                EmptyDataError(
                    f"No data rows found for dataflow '{dataflow}' with parameters: "
                    + f"{param_info}. "
                    + "The IMF constraints API reports this combination as valid, "
                    + "but no actual observations were returned in the data. "
                    + f"URL -> {url}"
                )
            )

        # Create DataFrame and clean up
        df = DataFrame(all_data_rows)
        df = df.rename(columns={"value": "OBS_VALUE"})
        df["OBS_VALUE"] = to_numeric(df["OBS_VALUE"], errors="coerce")

        # Parse TIME_PERIOD into valid date format
        if "TIME_PERIOD" in df.columns:
            df["TIME_PERIOD"] = df["TIME_PERIOD"].apply(parse_time_period)

        # Build metadata
        metadata: dict = {}

        # Get indicator descriptions from cache
        all_indicators_meta = self.metadata.get_indicators_in(dataflow)
        indicator_descriptions_map = {
            item["indicator"]: item["description"] for item in all_indicators_meta
        }

        # Add description column to DataFrame based on indicator code
        # Look for any indicator column to map descriptions
        indicator_col = None
        for col in df.columns:
            if col.endswith("_code") and col.replace("_code", "") in [
                "INDICATOR",
                "BOP_ACCOUNTING_ENTRY",
                "ACCOUNTING_ENTRY",
                "SERIES",
                "ITEM",
            ]:
                indicator_col = col
                break

        if indicator_col:
            df["description"] = df[indicator_col].map(indicator_descriptions_map)
        else:
            df["description"] = ""

        # Add indicator metadata
        for indicator_code in all_unique_indicators:
            # Use dataflow::indicator format for user-facing metadata keys
            full_key = f"{dataflow}::{indicator_code}"
            ind_meta = {
                "description": indicator_descriptions_map.get(indicator_code, ""),
                "indicator": indicator_code,
            }

            # Add derivation type to series metadata if available
            if indicator_code in all_series_derivation_types:
                ind_meta["derivation_type"] = all_series_derivation_types[
                    indicator_code
                ]

            metadata[full_key] = ind_meta

        # Add dataset-level metadata from cached dataflow info
        dataset_attrs = self._extract_dataset_attributes_from_cache(dataflow)

        if dataset_attrs:
            metadata["dataset"] = dataset_attrs

        return {"data": df.to_dict(orient="records"), "metadata": metadata}