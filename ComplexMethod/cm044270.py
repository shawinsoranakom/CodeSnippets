def to_dict(
        self,
        orient: Literal[
            "dict", "list", "series", "split", "tight", "records", "index"
        ] = "list",
    ) -> dict[Hashable, Any] | list[dict[Hashable, Any]]:
        """Convert results field to a dictionary using any of Pandas `to_dict` options.

        Parameters
        ----------
        orient : Literal["dict", "list", "series", "split", "tight", "records", "index"]
            Value to pass to `.to_dict()` method

        Returns
        -------
        Union[Dict[Hashable, Any], List[Dict[Hashable, Any]]]
            Dictionary of lists or list of dictionaries if orient is "records".
        """
        df = self.to_dataframe(index=None)
        if (
            orient == "list"
            and isinstance(self.results, dict)
            and all(
                isinstance(value, dict)
                for value in self.results.values()  # pylint: disable=no-member
            )
        ):
            df = df.T
        results: dict | list = df.to_dict(orient=orient)

        if isinstance(results, dict) and orient == "list" and "index" in results:
            del results["index"]

        return results