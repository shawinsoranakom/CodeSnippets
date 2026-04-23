async def get_one(URL):
            """Get the observations for a single date."""
            response = await amake_request(URL)
            data = [
                v
                for v in response.get("elements", {}).values()  # type: ignore
                if v.get("observation_value") != "." and v.get("type") != "header"
            ]
            if data:
                df = (
                    DataFrame(data)
                    .set_index(["line", "element_id", "parent_id"])
                    .sort_index()[
                        [
                            "level",
                            "series_id",
                            "name",
                            "observation_date",
                            "observation_value",
                        ]
                    ]
                    .reset_index()
                )
                df["parent_id"] = df.parent_id.astype(str)
                df["element_id"] = df.element_id.astype(str)
                df["observation_value"] = df.observation_value.str.replace(
                    ",", ""
                ).astype(float)
                df["line"] = df.line.astype(int)
                df["observation_date"] = to_datetime(
                    df["observation_date"], format="%b %Y"
                ).dt.date
                children = (
                    df.groupby("parent_id")["element_id"]
                    .apply(lambda x: x.sort_values().unique().tolist())
                    .to_dict()
                )
                children = {k: ",".join(v) for k, v in children.items()}
                df["children"] = df.element_id.map(children)
                df = (
                    df.set_index(
                        ["line", "element_id", "children", "parent_id", "level"]
                    )
                    .sort_index()
                    .reset_index()
                    .replace({nan: None})
                )
                if query.category == "personal_income":
                    df = df.set_index("line").sort_index()
                    df["units"] = "Bil. of $"
                    df.loc[35, "units"] = "%"
                    df.loc[36:37, "units"] = "Bil. of Chn. 2017 $"
                    df.loc[38, "units"] = "$"
                    df.loc[39, "units"] = "Chn. 2017"
                    df.loc[40, "units"] = "Thous."
                    df = df.reset_index()
                elif query.category in ["wages_by_industry", "pce_dollars"]:
                    df["units"] = "Bil. of $"
                elif query.category in [
                    "real_pce_percent_change",
                    "pce_price_percent_change",
                ]:
                    df["units"] = "%"
                elif query.category in ["real_pce_quantity_index", "pce_price_index"]:
                    df["units"] = "Index 2017=100"
                elif query.category == "real_pce_chained_dollars":
                    df["units"] = "Bil. of Chn. 2017 $"
                else:
                    pass

                results.extend(df.to_dict("records"))