async def run_node(self, role: Experimenter = None):
        if self.is_terminal() and role is not None:
            if role.state_saved:
                return self.raw_reward

        max_retries = 3
        num_runs = 1
        run_finished = False
        while num_runs <= max_retries and not run_finished:
            try:
                if not role:
                    role = self.load_role()
                    await load_execute_notebook(role)  # execute previous notebook's code
                    await role.run(with_message="continue")
                else:
                    await role.run(with_message=self.state["requirement"])
                score_dict = await role.get_score()
                score_dict = self.evaluate_simulation(score_dict)
                self.raw_reward = score_dict
                run_finished = True
            except TimeoutException as e:
                mcts_logger.log("MCTS", f"Role-level timeout: {e}")
                break
            except Exception as e:
                mcts_logger.log("MCTS", f"Error in running the role: {e}")
                num_runs += 1

        if not run_finished:
            mcts_logger.log("MCTS", f"Role {role.node_id} failed to run")
            if self.state["low_is_better"]:
                score_dict = {"test_score": np.inf, "dev_score": np.inf, "score": np.inf}
            else:
                score_dict = {"test_score": 0, "dev_score": 0, "score": 0}
            self.raw_reward = score_dict
        if self.state["low_is_better"]:
            # normalized the score to be between 0 and 1, and higher is better
            def normalize_score(score):
                if score == -1:
                    return 0
                return 1 / (1 + score)

            score_dict = {k: normalize_score(v) for k, v in score_dict.items()}
        self.normalized_reward = score_dict
        result_dict = role.get_solution()
        return score_dict, result_dict