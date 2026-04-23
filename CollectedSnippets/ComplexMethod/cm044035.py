def transform_query(params: dict[str, Any]) -> OECDGdpForecastQueryParams:
        """Transform the query."""
        transformed_params = params.copy()
        countries = transformed_params.get("country")
        new_countries: list = []
        freq = transformed_params.get("frequency")
        if not countries:
            new_countries.append("all")
        if countries:
            countries = (
                countries.split(",") if isinstance(countries, str) else countries
            )
            if "all" in countries:
                new_countries = ["all"]
            else:
                for country in countries:
                    if freq == "quarter":
                        if country.lower() in COUNTRIES_QUARTER:
                            new_countries.append(country.lower())
                        else:
                            warn(f"{country} is not available for quarterly data.")
                    else:  # noqa
                        if country.lower() in COUNTRIES:
                            new_countries.append(country.lower())
                        else:
                            warn(f"{country} is not available for annual data.")

        if not new_countries:
            raise OpenBBError(
                "No valid countries were found for the supplied parameters."
            )

        transformed_params["country"] = ",".join(new_countries)

        if not transformed_params.get("start_date"):
            transformed_params["start_date"] = datetime(
                datetime.today().year, 1, 1
            ).date()

        if not transformed_params.get("end_date"):
            transformed_params["end_date"] = datetime(
                datetime.today().year + 2, 12, 31
            ).date()

        return OECDGdpForecastQueryParams(**transformed_params)