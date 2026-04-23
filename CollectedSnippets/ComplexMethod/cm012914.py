def _generate_channels_table(
        self,
        filtered_data: OrderedDict[str, Any],
        channel_features: list[str],
        num_channels: int,
    ) -> tuple[list, list]:
        r"""
        Takes in the filtered data and features list and generates the channels headers and table

        Currently meant to generate the headers and table for both the channels information.

        Args:
            filtered_data (OrderedDict[str, Any]): An OrderedDict (sorted in order of model) mapping:
                module_fqns -> feature_names -> values
            channel_features (List[str]): A list of the channel level features
            num_channels (int): Number of channels in the channel data

        Returns a tuple with:
            A list of the headers of the channel table
            A list of lists containing the table information row by row
            The 0th index row will contain the headers of the columns
            The rest of the rows will contain data
        """
        # now we compose the table for the channel information table
        channel_table: list[list[Any]] = []
        channel_headers: list[str] = []

        # counter to keep track of number of entries in
        channel_table_entry_counter: int = 0

        if len(channel_features) > 0:
            # now we add all channel data
            for module_fqn in filtered_data:
                # we iterate over all channels
                for channel in range(num_channels):
                    # we make a new row for the channel
                    new_channel_row = [channel_table_entry_counter, module_fqn, channel]
                    for feature in channel_features:
                        if feature in filtered_data[module_fqn]:
                            # add value if applicable to module
                            feature_val = filtered_data[module_fqn][feature][channel]
                        else:
                            # add that it is not applicable
                            feature_val = "Not Applicable"

                        # if it's a tensor we want to extract val
                        if type(feature_val) is torch.Tensor:
                            feature_val = feature_val.item()

                        # add value to channel specific row
                        # pyrefly: ignore [bad-argument-type]
                        new_channel_row.append(feature_val)

                    # add to table and increment row index counter
                    channel_table.append(new_channel_row)
                    channel_table_entry_counter += 1

        # add row of headers of we actually have something, otherwise just empty
        if len(channel_table) != 0:
            channel_headers = ["idx", "layer_fqn", "channel"] + channel_features

        return (channel_headers, channel_table)