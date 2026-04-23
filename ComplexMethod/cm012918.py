def generate_detector_report(
        self, model: GraphModule
    ) -> tuple[str, dict[str, Any]]:
        r"""
        Determines whether input weight equalization is appropriate for a given module.

        Takes advantage of the ModelReport Observer which records the relevant percentile information

        Args:
            model (GraphModule): The prepared and calibrated GraphModule with inserted ModelReportObservers

        Returns a tuple with two elements:
            String report of of whether there are outliers in the activations around certain modules
            Dictionary mapping modules of interest to:
                whether there were outliers found in activation before
                the number of batches used for each channel
                whether fraction of applicable batches used is above fraction_batches_used_threshold
                their p_r metric compared to the threshold
                the threshold used to make the recommendation
                the reference_percentile used to make the recommendation
                the channel axis used to determine individual channels
                the constant batch counts per channel
                the per channel max values
        """
        # generate the information dictionary of outlier information
        info_dict = self._generate_info_dict(model)

        # now we can generate report based on this information
        outlier_string = "Outlier detection report: \n"

        # added module check
        added_module: bool = False

        # some strings to be formatted depending on module we are adding
        module_suggestion_str = "For Module {} looked at with axis {}: \n"
        channel_suggestion_str = "\tFor channel {}, we found outliers in the preceding activation data with {}.\n"
        channel_max_value_str = "a max value across all batches of {}"
        note_string = "Note: outlier detection is only reliable for {}. We recommend {} to ensure the most accurate results."
        note_distribution = "stationary distributions"
        note_rec = "running the static vs. dynamic detector to ensure activation data before modules above is stationary"

        # suggestion for constant batch check since that can make it no outliers
        constant_str = "\tFor channel {}, we found {} constant value batches. {}\n"
        constant_suggestion = "We recommend taking a look at the dict and data to see how frequent this occurred and why."

        # compile the suggestion string
        for module_fqn in info_dict:
            # get module specific info
            mod_info: dict[str, Any] = info_dict[module_fqn]
            # check to see if we already added high level model desc
            added_model_desc = False
            # look at each individual channel and add a suggestion
            for index, outlier_detected in enumerate(mod_info[self.OUTLIER_KEY]):
                if outlier_detected:
                    # we found at least 1 outlier
                    if not added_model_desc:
                        # add the module level description
                        outlier_string += module_suggestion_str.format(
                            module_fqn, self.ch_axis
                        )
                        added_model_desc = True

                    # we mark that we found at least one outlier
                    added_module = True
                    max_value_found_str = channel_max_value_str.format(
                        mod_info[self.MAX_VALS_KEY][index]
                    )
                    channel_str = channel_suggestion_str.format(
                        index, max_value_found_str
                    )
                    outlier_string += channel_str

                # also check if we found constant batch
                if mod_info[self.CONSTANT_COUNTS_KEY][index] != 0:
                    # make sure we add a module level highlight.
                    if not added_model_desc:
                        # add the module level description
                        outlier_string += module_suggestion_str.format(
                            module_fqn, self.ch_axis
                        )
                        added_model_desc = True

                    constant_values_for_channel = mod_info[self.CONSTANT_COUNTS_KEY][
                        index
                    ]
                    formatted_str = constant_str.format(
                        index, constant_values_for_channel, constant_suggestion
                    )
                    outlier_string += formatted_str
                    # we also added at least one thing to description
                    added_module = True

        # if found outlier, give suggestion, else give default response
        if added_module:
            # compose the note string
            note_composed = note_string.format(note_distribution, note_rec)
            outlier_string += note_composed
        else:
            outlier_string += "There were no outliers found in the activations.\n"

        return (outlier_string, info_dict)