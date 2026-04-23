def test_multiple_run_consistent_spike_outlier_report_gen(self):
        # specifically make a row really high consistently in the number of batches that you are testing and try that
        # generate report after just 1 run, and after many runs (30) and make sure above minimum threshold is there
        with override_quantized_engine('fbgemm'):

            # detector of interest
            outlier_detector = OutlierDetector(reference_percentile=0.95)

            param_size: int = 8
            detector_set = {outlier_detector}
            model = self.LargeBatchModel(param_size=param_size)

            # get tst model and calibrate
            prepared_for_callibrate_model, mod_report = self._get_prepped_for_calibration_model(
                model, detector_set, use_outlier_data=True
            )

            # now we actually calibrate the model
            example_input = model.get_outlier_inputs()[0]
            example_input = example_input.to(torch.float)

            # now calibrate minimum 30 times to make it above minimum threshold
            for i in range(30):
                example_input = model.get_outlier_inputs()[0]
                example_input = example_input.to(torch.float)

                # make 2 of the batches to have zero channel
                if i % 14 == 0:
                    # make one channel constant
                    example_input[0][1] = torch.zeros_like(example_input[0][1])

                prepared_for_callibrate_model(example_input)

            # now get the report by running it through ModelReport instance
            generated_report = mod_report.generate_model_report(True)

            # check that sizes are appropriate only 1 detector
            self.assertEqual(len(generated_report), 1)

            # get the specific report for input weight equalization
            outlier_str, outlier_dict = generated_report[outlier_detector.get_detector_name()]

            # we should have 5 layers looked at since 4 conv + linear + relu
            self.assertEqual(len(outlier_dict), 4)

            # assert the following are true for all the modules
            for module_fqn in outlier_dict:
                # get the info for the specific module
                module_dict = outlier_dict[module_fqn]

                # because we ran 30 times, we should have at least a couple be significant
                # could be less because some channels could possibly be all 0
                sufficient_batches_info = module_dict[OutlierDetector.IS_SUFFICIENT_BATCHES_KEY]
                if not sum(sufficient_batches_info) >= len(sufficient_batches_info) / 2:
                    raise AssertionError(
                        f"Expected at least half of channels to have sufficient batches, "
                        f"got {sum(sufficient_batches_info)} out of {len(sufficient_batches_info)}"
                    )

                # half of them should be outliers, because we set a really high value every 2 channels
                outlier_info = module_dict[OutlierDetector.OUTLIER_KEY]
                self.assertEqual(sum(outlier_info), len(outlier_info) / 2)

                # ensure that the number of ratios and batches counted is the same as the number of params
                self.assertEqual(len(module_dict[OutlierDetector.COMP_METRIC_KEY]), param_size)
                self.assertEqual(len(module_dict[OutlierDetector.NUM_BATCHES_KEY]), param_size)

                # for the first one ensure the per channel max values are what we set
                if module_fqn == "linear.0":

                    # check that the non-zero channel count, at least 2 should be there
                    # for the first module
                    counts_info = module_dict[OutlierDetector.CONSTANT_COUNTS_KEY]
                    if not sum(counts_info) >= 2:
                        raise AssertionError(
                            f"Expected at least 2 non-zero channel counts, got {sum(counts_info)}"
                        )

                    # half of the recorded max values should be what we set
                    matched_max = sum(val == 3.28e8 for val in module_dict[OutlierDetector.MAX_VALS_KEY])
                    self.assertEqual(matched_max, param_size / 2)