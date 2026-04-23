def run_actor(self, actor_id: str, run_input: dict, fields: list[str] | None = None) -> list[dict]:
        """Run an Apify Actor and return the output dataset.

        Args:
            actor_id: Actor name from Apify store to run.
            run_input: JSON input for the Actor.
            fields: List of fields to extract from the dataset. Other fields will be ignored.
        """
        client = self._get_apify_client()
        if (details := client.actor(actor_id=actor_id).call(run_input=run_input, wait_secs=1)) is None:
            msg = "Actor run details not found"
            raise ValueError(msg)
        if (run_id := details.get("id")) is None:
            msg = "Run id not found"
            raise ValueError(msg)

        if (run_client := client.run(run_id)) is None:
            msg = "Run client not found"
            raise ValueError(msg)

        # stream logs
        with run_client.log().stream() as response:
            if response:
                for line in response.iter_lines():
                    self.log(line)
        run_client.wait_for_finish()

        dataset_id = self._get_run_dataset_id(run_id)

        loader = ApifyDatasetLoader(
            dataset_id=dataset_id,
            dataset_mapping_function=lambda item: item
            if not fields
            else {k.replace(".", "_"): ApifyActorsComponent.get_nested_value(item, k) for k in fields},
        )
        return loader.load()