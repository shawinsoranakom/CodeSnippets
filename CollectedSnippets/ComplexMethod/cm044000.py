async def get_one_country(_country):
            """Get the GDP data for one country."""
            _country = (
                _country.upper()
                if len(_country) == 2
                else COUNTRY_MAP[_country.lower()]
            )
            final_df = DataFrame()
            gdp_response, gdp_qoq_response, gdp_yoy_response = await asyncio.gather(
                get_context(
                    "GDP",
                    _country,
                    None if _country == "US" else "TUSD",
                    query.use_cache,
                ),
                get_context("GDP", _country, "TPOP", query.use_cache),
                get_context("GDP", _country, "TOYA", query.use_cache),
            )
            gdp = parse_context(gdp_response, latest=False).rename(columns={"GDP": "value"})  # type: ignore
            gdp_qoq = parse_context(gdp_qoq_response, latest=False).rename(columns={"GDP": "nominal_growth_qoq"})  # type: ignore
            gdp_yoy = parse_context(gdp_yoy_response, latest=False).rename(columns={"GDP": "nominal_growth_yoy"})  # type: ignore
            gdp = (
                gdp.set_index("Country", append=True)
                if "Country" in gdp.columns
                else gdp
            )
            gdp_qoq = (
                gdp_qoq.set_index("Country", append=True)
                if "Country" in gdp_qoq.columns
                else gdp_qoq
            )
            gdp_yoy = (
                gdp_yoy.set_index("Country", append=True)
                if "Country" in gdp_yoy.columns
                else gdp_yoy
            )
            final_df = concat(
                [gdp, gdp_qoq, gdp_yoy],
                axis=1,
            )
            if final_df.empty:
                warn(f"Error: No data returned for {_country}.")
            if not final_df.empty:
                results.extend(
                    final_df.reset_index()
                    .rename(columns={"Country": "country"})
                    .to_dict(orient="records")
                )