def generate_model_report(
        self, remove_inserted_observers: bool
    ) -> dict[str, tuple[str, dict]]:
        r"""
        Generates all the requested reports.

        Note:
            You should have calibrated the model with relevant data before calling this

        The reports generated are specified by the desired_reports specified in desired_reports

        Can optionally remove all the observers inserted by the ModelReport instance

        Args:
            remove_inserted_observers (bool): True to remove the observers inserted by this ModelReport instance

        Returns a mapping of each desired report name to a tuple with:
            The textual summary of that report information
            A dictionary containing relevant statistics or information for that report

        Note:
            Throws exception if we try to generate report on model we already removed observers from
            Throws exception if we try to generate report without preparing for calibration
        """
        # if we haven't prepped model for calibration, then we shouldn't generate report yet
        if not self._prepared_flag:
            raise Exception(  # noqa: TRY002
                "Cannot generate report without preparing model for calibration"
            )

        # if we already removed the observers, we cannot generate report
        if self._removed_observers:
            raise Exception(  # noqa: TRY002
                "Cannot generate report on model you already removed observers from"
            )

        # keep track of all the reports of interest and their outputs
        reports_of_interest = {}

        for detector in self._desired_report_detectors:
            # generate the individual report for the detector
            report_output = detector.generate_detector_report(self._model)
            reports_of_interest[detector.get_detector_name()] = report_output

        # if user wishes to remove inserted observers, go ahead and remove
        if remove_inserted_observers:
            self._removed_observers = True
            # get the set of all Observers inserted by this instance of ModelReport
            all_observers_of_interest: set[str] = set()
            for desired_report in self._detector_name_to_observer_fqns:
                observers_of_interest = self._detector_name_to_observer_fqns[
                    desired_report
                ]
                all_observers_of_interest.update(observers_of_interest)

            # go through all_observers_of_interest and remove them from the graph and model
            for observer_fqn in all_observers_of_interest:
                # remove the observer from the model
                self._model.delete_submodule(observer_fqn)

                # remove the observer from the graph structure
                node_obj = self._get_node_from_fqn(observer_fqn)

                if node_obj:
                    self._model.graph.erase_node(node_obj)
                else:
                    raise ValueError("Node no longer exists in GraphModule structure")

            # remember to recompile the model
            self._model.recompile()

        # save the generated reports for visualization purposes
        saved_reports: dict[str, dict] = {
            report_name: report_tuple[1]
            for report_name, report_tuple in reports_of_interest.items()
        }

        self._generated_reports = saved_reports

        # return the reports of interest
        return reports_of_interest