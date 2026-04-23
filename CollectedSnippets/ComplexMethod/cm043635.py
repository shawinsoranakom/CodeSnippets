async def get_one(URL):
            """Get the observations for a single date."""
            response = await amake_request(URL)
            data = [v for v in response.get("elements", {}).values() if v.get("observation_value") != "."]  # type: ignore
            if data:
                df = (
                    DataFrame(data)
                    .set_index(["element_id", "parent_id"])
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
                if query.category.startswith(
                    "employees"
                ) and not query.category.endswith("percent"):
                    df["observation_value"] = df.observation_value * 1000
                elif query.category.endswith("percent"):
                    df["observation_value"] = df.observation_value / 100

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
                    df.set_index(["element_id", "children", "parent_id", "level"])
                    .sort_index()
                    .reset_index()
                    .replace({nan: None})
                )
                results.extend(df.to_dict("records"))