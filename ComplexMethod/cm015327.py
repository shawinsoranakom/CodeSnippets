def test_prepare_model_callibration(self):
        """
        Tests model_report.prepare_detailed_calibration that prepares the model for calibration
        Specifically looks at:
        - Whether observers are properly inserted into regular nn.Module
        - Whether the target and the arguments of the observers are proper
        - Whether the internal representation of observers of interest is updated
        """

        with override_quantized_engine('fbgemm'):
            # create model report object

            # create model
            model = TwoThreeOps()
            # make an example set of detectors
            torch.backends.quantized.engine = "fbgemm"
            backend = torch.backends.quantized.engine
            test_detector_set = {DynamicStaticDetector(), PerChannelDetector(backend)}
            # initialize with an empty detector

            # prepare the model
            example_input = model.get_example_inputs()[0]
            current_backend = torch.backends.quantized.engine
            q_config_mapping = QConfigMapping()
            q_config_mapping.set_global(torch.ao.quantization.get_default_qconfig(torch.backends.quantized.engine))

            model_prep = quantize_fx.prepare_fx(model, q_config_mapping, example_input)

            model_report = ModelReport(model_prep, test_detector_set)

            # prepare the model for calibration
            prepared_for_callibrate_model = model_report.prepare_detailed_calibration()

            # see whether observers properly in regular nn.Module
            # there should be 4 observers present in this case
            modules_observer_cnt = 0
            for module in prepared_for_callibrate_model.modules():
                if isinstance(module, ModelReportObserver):
                    modules_observer_cnt += 1

            self.assertEqual(modules_observer_cnt, 4)

            model_report_str_check = "model_report"
            # also make sure arguments for observers in the graph are proper
            for node in prepared_for_callibrate_model.graph.nodes:
                # not all node targets are strings, so check
                if isinstance(node.target, str) and model_report_str_check in node.target:
                    # if pre-observer has same args as the linear (next node)
                    if "pre_observer" in node.target:
                        self.assertEqual(node.args, node.next.args)
                    # if post-observer, args are the target linear (previous node)
                    if "post_observer" in node.target:
                        self.assertEqual(node.args, (node.prev,))

            # ensure model_report observers of interest updated
            # there should be two entries
            self.assertEqual(len(model_report.get_observers_of_interest()), 2)
            for detector in test_detector_set:
                self.assertTrue(detector.get_detector_name() in model_report.get_observers_of_interest())

                # get number of entries for this detector
                detector_obs_of_interest_fqns = model_report.get_observers_of_interest()[detector.get_detector_name()]

                # assert that the per channel detector has 0 and the dynamic static has 4
                if isinstance(detector, PerChannelDetector):
                    self.assertEqual(len(detector_obs_of_interest_fqns), 0)
                elif isinstance(detector, DynamicStaticDetector):
                    self.assertEqual(len(detector_obs_of_interest_fqns), 4)

            # ensure that we can prepare for calibration only once
            with self.assertRaises(ValueError):
                prepared_for_callibrate_model = model_report.prepare_detailed_calibration()