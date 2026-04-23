def _add_jsonpath_inspection_data(self, env: TestStateEnvironment):

        state = self._wrapped

        if not isinstance(state, StatePass):
            if not self.is_single_state:
                return

            if "afterInputPath" not in env.inspection_data:
                env.inspection_data["afterInputPath"] = env.states.get_input()
            return

        # If not a terminal state, only populate inspection data from pre-processor.
        if not isinstance(self._wrapped.continue_with, ContinueWithEnd):
            return

        if state.result:
            # TODO: investigate interactions between these inspectionData field types.
            # i.e parity tests shows that if "Result" is defined, 'afterInputPath' and 'afterParameters'
            # cannot be present in the inspection data.
            env.inspection_data.pop("afterInputPath", None)
            env.inspection_data.pop("afterParameters", None)

            if "afterResultSelector" not in env.inspection_data:
                env.inspection_data["afterResultSelector"] = state.result.result_obj

            if "afterResultPath" not in env.inspection_data:
                env.inspection_data["afterResultPath"] = env.inspection_data.get(
                    "afterResultSelector", env.states.get_input()
                )
            return

        if "afterInputPath" not in env.inspection_data:
            env.inspection_data["afterInputPath"] = env.states.get_input()

        if "afterParameters" not in env.inspection_data:
            env.inspection_data["afterParameters"] = env.inspection_data.get(
                "afterInputPath", env.states.get_input()
            )

        if "afterResultSelector" not in env.inspection_data:
            env.inspection_data["afterResultSelector"] = env.inspection_data["afterParameters"]

        if "afterResultPath" not in env.inspection_data:
            env.inspection_data["afterResultPath"] = env.inspection_data.get(
                "afterResultSelector", env.states.get_input()
            )