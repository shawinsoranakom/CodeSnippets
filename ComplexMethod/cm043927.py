def search_indicators(
        self,
        query: str,
        dataflows: list[str] | str | None = None,
        keywords: list[str] | None = None,
    ) -> list[dict]:
        """Search indicators based on a query string and optional keyword filters.

        Parameters
        ----------
        query : str
            The search query string. Multiple search phrases can be separated by semicolons (;).
            Each phrase can use AND (+) and OR (|) operators, as well as quoted phrases.
            Semicolon separation allows commas to be used within search phrases.
            Examples:
                "inflation rate;+consumer price" - searches for "inflation rate" OR "consumer price"
                "gdp+growth;|employment" - searches for "gdp AND growth" OR "employment"
        dataflows : list[str] | str | None, optional
            A dataflow ID or list of dataflow IDs to search within. If None, all
            dataflows will be searched, which can be slow.
        keywords : list[str] | None, optional
            List of keywords to filter results. Each keyword is a single word that must
            appear in the indicator's label or description. Keywords prefixed with "not "
            will exclude indicators containing that word (e.g., "not USD" excludes indicators
            with "USD" in them).
        Returns
        -------
        list[dict]
            A list of matching indicators with table/hierarchy information included.
        """
        target_dataflow_ids: list = []
        if dataflows:
            target_dataflow_ids = (
                [dataflows] if isinstance(dataflows, str) else dataflows
            )
        else:
            if not query and not keywords:
                raise OpenBBError(
                    "A query must be provided when no dataflows and keywords are specified."
                )
            target_dataflow_ids = list(self.dataflows.keys())

        if not target_dataflow_ids:
            raise OpenBBError(
                "No valid dataflows found to search indicators in."
                "This might be due to incorrect dataflow IDs."
            )

        # Build a map of indicators to their tables for enrichment
        indicator_to_tables: dict[str, list[dict]] = {}
        # Also build searchable text for each indicator from their tables
        indicator_table_text: dict[str, str] = {}

        for df_id in set(target_dataflow_ids):
            try:
                hierarchies = self.get_dataflow_hierarchies(df_id)
                for hierarchy in hierarchies:
                    try:
                        structure = self.get_dataflow_table_structure(
                            df_id, hierarchy["id"]
                        )
                        # Build searchable table text
                        table_search_text = (
                            hierarchy.get("name", "").lower()
                            + " "
                            + hierarchy.get("description", "").lower()
                        )

                        for ind in structure.get("indicators", []):
                            if ind.get("is_group"):
                                continue
                            indicator_code = ind.get("indicator_code") or ind.get(
                                "code"
                            )
                            if indicator_code:
                                key = f"{df_id}_{indicator_code}"
                                if key not in indicator_to_tables:
                                    indicator_to_tables[key] = []
                                    indicator_table_text[key] = ""

                                table_entry = {
                                    "table_id": hierarchy["id"],
                                    "table_name": hierarchy["name"],
                                }
                                if table_entry not in indicator_to_tables[key]:
                                    indicator_to_tables[key].append(table_entry)
                                    indicator_table_text[key] += " " + table_search_text
                    except Exception:  # noqa: S110
                        pass
            except Exception:  # noqa: S110
                pass

        # Get indicators for target dataflows
        all_indicators: list = []
        for df_id in set(target_dataflow_ids):
            try:
                indicators = self.get_indicators_in(df_id)
                # Enrich each indicator with table information
                for ind in indicators:
                    key = f"{df_id}_{ind['indicator']}"
                    ind["tables"] = indicator_to_tables.get(key, [])
                    # Build member_of as list of dataflow_id::table_id strings
                    ind["member_of"] = [
                        f"{df_id}::{t['table_id']}" for t in ind["tables"]
                    ]
                    # Add table text for searching (will be removed before return)
                    ind["_table_search_text"] = indicator_table_text.get(key, "")
                all_indicators.extend(indicators)
            except (KeyError, ValueError, OpenBBError) as e:
                warnings.warn(
                    f"Could not retrieve indicators for dataflow '{df_id}': {e}",
                    OpenBBWarning,
                )
                continue

        # Filter indicators by query
        # Split query on semicolon to allow commas within search phrases
        if not query:
            search_results = all_indicators
        else:
            # Split on semicolon to get separate phrases
            phrases = [phrase.strip() for phrase in query.split(";") if phrase.strip()]

            if not phrases:
                search_results = all_indicators
            else:
                filtered_by_query: list = []
                for indicator in all_indicators:
                    text_to_search = (
                        indicator.get("label", "").lower()
                        + " "
                        + indicator.get("description", "").lower()
                        + " "
                        + indicator.get("dataflow_name", "").lower()
                        + " "
                        + indicator.get("dataflow_id", "").lower()
                        + " "
                        + indicator.get("indicator", "").lower()
                        + " "
                        + indicator.get("_table_search_text", "")
                    )

                    match = False
                    for phrase in phrases:
                        # This handles AND (+) and OR (|) operators within the phrase
                        parsed_phrase = self._parse_query(phrase)

                        if not parsed_phrase:
                            # If parsing fails, treat as simple substring search
                            if phrase.lower() in text_to_search:
                                match = True
                                break
                        else:
                            phrase_match = False

                            for or_group in parsed_phrase:
                                if all(term in text_to_search for term in or_group):
                                    phrase_match = True
                                    break

                            if phrase_match:
                                match = True
                                break

                    if match:
                        filtered_by_query.append(indicator)
                search_results = filtered_by_query

        # Apply keyword filters
        if not keywords:
            # Clean up internal search field before returning
            for indicator in search_results:
                indicator.pop("_table_search_text", None)
            return search_results

        filtered_results: list = []
        for indicator in search_results:
            indicator_text = (
                indicator.get("indicator", "")
                + " "
                + indicator.get("label", "")
                + " "
                + indicator.get("description", "")
                + " "
                + indicator.get("_table_search_text", "")
            ).lower()

            # Check each keyword
            include = True
            for keyword in keywords:
                kw = keyword.strip()
                if kw.lower().startswith("not "):
                    # Exclusion keyword - if the word is present, exclude this indicator
                    exclude_word = kw[4:].lower()  # Remove "not " prefix
                    if exclude_word and exclude_word in indicator_text:
                        include = False
                        break
                elif kw.lower() not in indicator_text:
                    include = False
                    break

            if include:
                filtered_results.append(indicator)

        # Clean up internal search field before returning
        for indicator in filtered_results:
            indicator.pop("_table_search_text", None)

        return filtered_results