def mock_data(
        dataset: Literal["timeseries", "panel"],
        size: int = 5,
        sample: dict[str, Any] | None = None,
        multiindex: dict[str, Any] | None = None,
    ) -> list[dict]:
        """Generate mock data from a sample.

        Parameters
        ----------
        dataset : str
            The type of data to return:
            - 'timeseries': Time series data
            - 'panel': Panel data (multiindex)

        size : int
            The size of the data to return, default is 5.
        sample : Optional[Dict[str, Any]], optional
            A sample of the data to return, by default None.
        multiindex_names : Optional[List[str]], optional
            The names of the multiindex, by default None.

        Timeseries default sample:
        {
            "date": "2023-01-01",
            "open": 110.0,
            "high": 120.0,
            "low": 100.0,
            "close": 115.0,
            "volume": 10000,
        }

        Panel default sample:
        {
            "portfolio_value": 100000,
            "risk_free_rate": 0.02,
        }
        multiindex: {"asset_manager": "AM", "time": 0}

        Returns
        -------
        List[Dict]
            A list of dictionaries with the mock data.
        """
        if dataset == "timeseries":
            sample = sample or {
                "date": "2023-01-01",
                "open": 110.0,
                "high": 120.0,
                "low": 100.0,
                "close": 115.0,
                "volume": 10000,
            }
            result = []
            for i in range(1, size + 1):
                s = APIEx._shift(i)
                obs = {}
                for k, v in sample.items():
                    if k == "date":
                        obs[k] = (
                            datetime.strptime(v, "%Y-%m-%d") + timedelta(days=i)
                        ).strftime("%Y-%m-%d")
                    else:
                        obs[k] = round(v * s, 2)
                result.append(obs)
            return result
        if dataset == "panel":
            sample = sample or {
                "portfolio_value": 100000.0,
                "risk_free_rate": 0.02,
            }
            multiindex = multiindex or {"asset_manager": "AM", "time": 0}
            multiindex_names = list(multiindex.keys())
            idx_1 = multiindex_names[0]
            idx_2 = multiindex_names[1]
            items_per_idx = 2
            item: dict[str, Any] = {
                "is_multiindex": True,
                "multiindex_names": str(multiindex_names),
            }
            # Iterate over the number of items to create and add them to the result
            result = []
            for i in range(1, size + 1):
                item[idx_1] = f"{idx_1}_{i}"
                for j in range(items_per_idx):
                    item[idx_2] = j
                    for k, v in sample.items():
                        if isinstance(v, str):
                            item[k] = f"{v}_{j}"
                        else:
                            item[k] = round(v * APIEx._shift(i + j), 2)
                    result.append(item.copy())
            return result
        raise ValueError(f"Dataset '{dataset}' not found.")