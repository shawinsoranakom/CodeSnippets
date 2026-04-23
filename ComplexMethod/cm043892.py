async def aextract_data(
        query: ImfConsumerPriceIndexQueryParams,
        credentials: dict[str, str] | None,
        **kwargs: Any,
    ) -> dict:
        """Extract data."""
        countries = query.country.split(",")
        countries_str = (
            "*" if "*" in countries else "+".join([c.upper() for c in countries])
        )
        index_type = "HICP" if query.harmonized is True else "CPI"
        expenditures = query.expenditure.split(",") if query.expenditure else ["total"]
        expenditures_str = (
            "*"
            if "all" in expenditures
            else "+".join(
                [
                    (
                        e.upper()
                        if e.upper() in expenditure_dict_rev
                        else expenditure_dict[e]
                    )
                    for e in expenditures
                ]
            )
        )
        parameters: dict = {
            "COUNTRY": countries_str,
            "INDEX_TYPE": index_type,
            "COICOP_1999": expenditures_str,
            "TYPE_OF_TRANSFORMATION": transformation_map[query.transform],
            "FREQUENCY": query.frequency[0].upper(),
        }
        query_builder = ImfQueryBuilder()

        # Mappings from IMF dimension codes to user-friendly parameter names
        dim_to_param = {
            "COUNTRY": "country",
            "INDEX_TYPE": "harmonized",
            "COICOP_1999": "expenditure",
            "TYPE_OF_TRANSFORMATION": "transform",
            "FREQUENCY": "frequency",
        }
        # Reverse mappings for values
        transformation_rev = {v: k for k, v in transformation_map.items()}
        frequency_map = {"A": "annual", "Q": "quarter", "M": "monthly"}

        if query.limit is not None:
            parameters["lastNObservations"] = query.limit

        try:
            data = query_builder.fetch_data(
                dataflow="CPI",
                start_date=(
                    query.start_date.strftime("%Y-%m-%d") if query.start_date else None
                ),
                end_date=(
                    query.end_date.strftime("%Y-%m-%d") if query.end_date else None
                ),
                **parameters,
            )
        except ValueError as e:
            # Translate dimension codes to user-friendly parameter names in error message
            error_msg = str(e)
            for dim_code, param_name in dim_to_param.items():
                error_msg = error_msg.replace(f"'{dim_code}'", f"'{param_name}'")
                error_msg = error_msg.replace(f'"{dim_code}"', f'"{param_name}"')
            # Translate transformation values
            for api_val, user_val in transformation_rev.items():
                error_msg = error_msg.replace(f"'{api_val}'", f"'{user_val}'")
            # Translate frequency values
            for api_val, user_val in frequency_map.items():
                error_msg = error_msg.replace(f"'{api_val}'", f"'{user_val}'")
            # Translate expenditure values
            for api_val, user_val in expenditure_dict_rev.items():
                error_msg = error_msg.replace(f"'{api_val}'", f"'{user_val}'")
            # Translate INDEX_TYPE values
            error_msg = error_msg.replace("'CPI'", "'False'")
            error_msg = error_msg.replace("'HICP'", "'True'")
            # Translate country codes back to user-friendly names
            for code, label in CPI_CODE_TO_LABEL.items():
                error_msg = error_msg.replace(f"'{code}'", f"'{label}'")
            raise OpenBBError(error_msg) from e
        except OpenBBError as e:
            raise OpenBBError(e) from e

        return data