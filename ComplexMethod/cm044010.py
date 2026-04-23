async def get_one_country(_country):  # pylint: disable=too-many-locals
            """Get the profile for one country."""
            _country = _country.upper()
            final_df = DataFrame()
            (
                gdp_response,
                gdp_qoq_response,
                gdp_yoy_response,
                pop_response,
                cpi_response,
                core_response,
                retail_response,
                industrial_response,
                policy_response,
                y10y_response,
                gdebt_response,
                ca_response,
                urate_response,
            ) = await asyncio.gather(
                get_context("GDP", _country, "TUSD", use_cache),
                get_context("RGDP", _country, "TPOP", use_cache),
                get_context("RGDP", _country, "TOYA", use_cache),
                get_context("POP", _country, None, use_cache),
                get_context("CPI", _country, "TOYA", use_cache),
                get_context("CORE", _country, "TOYA", use_cache),
                get_context("RETA", _country, "TOYA", use_cache),
                get_context("IP", _country, "TOYA", use_cache),
                get_context("POLIR", _country, None, use_cache),
                get_context("Y10YD", _country, None, use_cache),
                get_context("GDEBT", _country, "TUSD", use_cache),
                get_context("CA", _country, "TPGP", use_cache),
                get_context("URATE", _country, None, use_cache),
            )
            gdp = parse_context(gdp_response, latest=latest).rename(columns={"GDP": "GDP ($B USD)"})  # type: ignore
            gdp_qoq = parse_context(gdp_qoq_response, latest=latest).rename(columns={"RGDP": "GDP QoQ"})  # type: ignore
            gdp_yoy = parse_context(gdp_yoy_response, latest=latest).rename(columns={"RGDP": "GDP YoY"})  # type: ignore
            pop = parse_context(pop_response, latest=latest).rename(columns={"POP": "Population"})  # type: ignore
            cpi = parse_context(cpi_response, latest=latest).rename(columns={"CPI": "CPI YoY"})  # type: ignore
            core_cpi = parse_context(core_response, latest=latest).rename(columns={"CORE": "Core CPI YoY"})  # type: ignore
            retail_sales = parse_context(retail_response, latest=latest).rename(columns={"RETA": "Retail Sales YoY"})  # type: ignore
            industrial_production = parse_context(
                industrial_response, latest=latest
            ).rename(
                columns={"IP": "Industrial Production YoY"}
            )  # type: ignore
            policy_rate = parse_context(policy_response, latest=latest).rename(columns={"POLIR": "Policy Rate"})  # type: ignore
            y10y = parse_context(y10y_response, latest=latest).rename(columns={"Y10YD": "10Y Yield"})  # type: ignore
            gdebt = parse_context(gdebt_response, latest=latest).rename(columns={"GDEBT": "Govt Debt/GDP"})  # type: ignore
            ca = parse_context(ca_response, latest=latest).rename(columns={"CA": "Current Account/GDP"})  # type: ignore
            urate = parse_context(urate_response, latest=latest).rename(columns={"URATE": "Jobless Rate"})  # type: ignore
            # If returning a pivot table, we need to add the country as an index before concatenating.
            if latest is False:
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
                pop = (
                    pop.set_index("Country", append=True)
                    if "Country" in pop.columns
                    else pop
                )
                cpi = (
                    cpi.set_index("Country", append=True)
                    if "Country" in cpi.columns
                    else cpi
                )
                core_cpi = (
                    core_cpi.set_index("Country", append=True)
                    if "Country" in core_cpi.columns
                    else core_cpi
                )
                retail_sales = (
                    retail_sales.set_index("Country", append=True)
                    if "Country" in retail_sales.columns
                    else retail_sales
                )
                industrial_production = (
                    industrial_production.set_index("Country", append=True)
                    if "Country" in industrial_production.columns
                    else industrial_production
                )
                policy_rate = (
                    policy_rate.set_index("Country", append=True)
                    if "Country" in policy_rate.columns
                    else policy_rate
                )
                y10y = (
                    y10y.set_index("Country", append=True)
                    if "Country" in y10y.columns
                    else y10y
                )
                gdebt = (
                    gdebt.set_index("Country", append=True)
                    if "Country" in gdebt.columns
                    else gdebt
                )
                ca = (
                    ca.set_index("Country", append=True)
                    if "Country" in ca.columns
                    else ca
                )
                urate = (
                    urate.set_index("Country", append=True)
                    if "Country" in urate.columns
                    else urate
                )
            final_df = concat(
                [
                    gdp,
                    gdp_qoq,
                    gdp_yoy,
                    cpi,
                    core_cpi,
                    retail_sales,
                    industrial_production,
                    policy_rate,
                    y10y,
                    gdebt,
                    ca,
                    urate,
                    pop,
                ],
                axis=1,
            )
            # Here, calculating this ratio ourselves produces better results than directly transforming from the API.
            if (
                "Govt Debt/GDP" in final_df.columns
                and "GDP ($B USD)" in final_df.columns
            ):
                final_df["Govt Debt/GDP"] = (
                    final_df["Govt Debt/GDP"] / final_df["GDP ($B USD)"]
                )
            if "Current Account/GDP" in final_df.columns and _country == "US":
                final_df["Current Account/GDP"] = final_df["Current Account/GDP"] * 4
            if final_df.empty:
                warn(f"Error: No data returned for {_country}.")
            if not final_df.empty:
                results.extend(final_df.reset_index().to_dict(orient="records"))