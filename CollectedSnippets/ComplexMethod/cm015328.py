def test_input_weight_equalization_determine_points(self):
        # use fbgemm and create our model instance
        # then create model report instance with detector
        with override_quantized_engine('fbgemm'):

            detector_set = {InputWeightEqualizationDetector(0.5)}

            # get tst model and calibrate
            non_fused = self._get_prepped_for_calibration_model(self.TwoBlockComplexNet(), detector_set)
            fused = self._get_prepped_for_calibration_model(self.TwoBlockComplexNet(), detector_set, fused=True)

            # reporter should still give same counts even for fused model
            for prepared_for_callibrate_model, _mod_report in [non_fused, fused]:

                # supported modules to check
                mods_to_check = {nn.Linear, nn.Conv2d}

                # get the set of all nodes in the graph their fqns
                node_fqns = {node.target for node in prepared_for_callibrate_model.graph.nodes}

                # there should be 4 node fqns that have the observer inserted
                correct_number_of_obs_inserted = 4
                number_of_obs_found = 0
                obs_name_to_find = InputWeightEqualizationDetector.DEFAULT_PRE_OBSERVER_NAME

                for node in prepared_for_callibrate_model.graph.nodes:
                    # if the obs name is inside the target, we found an observer
                    if obs_name_to_find in str(node.target):
                        number_of_obs_found += 1

                self.assertEqual(number_of_obs_found, correct_number_of_obs_inserted)

                # assert that each of the desired modules have the observers inserted
                for module in prepared_for_callibrate_model.modules():
                    # check if module is a supported module
                    is_in_include_list = sum(isinstance(module, x) for x in mods_to_check) > 0

                    if is_in_include_list:
                        # make sure it has the observer attribute
                        self.assertTrue(hasattr(module, InputWeightEqualizationDetector.DEFAULT_PRE_OBSERVER_NAME))
                    else:
                        # if it's not a supported type, it shouldn't have observer attached
                        self.assertTrue(not hasattr(module, InputWeightEqualizationDetector.DEFAULT_PRE_OBSERVER_NAME))