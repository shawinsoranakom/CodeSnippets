def hook(module, input) -> None:
            input_data = input[0]

            data = self.data_groups[name].get("data")  # aggregated data
            if features is None:
                # no features associated, data should not be a list
                if data is None:
                    data = torch.zeros_like(input_data)
                    self.state[name]["mask"] = torch.ones_like(input_data)
                out_data = agg_fn(data, input_data)
            else:
                # data should be a list [aggregated over each feature only]
                if data is None:
                    out_data = [
                        0 for _ in range(len(features))
                    ]  # create one in case of 1st forward
                    self.state[name]["mask"] = [0 for _ in range(len(features))]
                else:
                    out_data = data  # a list

                # compute aggregate over each feature
                for feature_idx in range(len(features)):
                    # each feature is either a list or scalar, convert it to torch tensor
                    feature_tensor = (
                        torch.Tensor([features[feature_idx]])
                        .long()
                        .to(input_data.device)
                    )
                    data_feature = torch.index_select(
                        input_data, feature_dim, feature_tensor
                    )
                    if data is None:
                        curr_data = torch.zeros_like(data_feature)
                        self.state[name]["mask"][feature_idx] = torch.ones_like(
                            data_feature
                        )
                    else:
                        curr_data = data[feature_idx]
                    out_data[feature_idx] = agg_fn(curr_data, data_feature)
            self.data_groups[name]["data"] = out_data