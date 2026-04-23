def set_epoch_as_seed(self, seed, dataset_config):
        if self.mode == "train":
            try:
                border_map_id = [
                    index
                    for index, dictionary in enumerate(dataset_config["transforms"])
                    if "MakeBorderMap" in dictionary
                ][0]
                shrink_map_id = [
                    index
                    for index, dictionary in enumerate(dataset_config["transforms"])
                    if "MakeShrinkMap" in dictionary
                ][0]
                dataset_config["transforms"][border_map_id]["MakeBorderMap"][
                    "epoch"
                ] = (seed if seed is not None else 0)
                dataset_config["transforms"][shrink_map_id]["MakeShrinkMap"][
                    "epoch"
                ] = (seed if seed is not None else 0)
            except Exception as E:
                print(E)
                return