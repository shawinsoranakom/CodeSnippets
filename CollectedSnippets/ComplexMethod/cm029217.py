def _update_plan_from_model_output(self, model_output: AgentOutput) -> None:
		"""Update the plan state from model output fields (current_plan_item, plan_update)."""
		if not self.settings.enable_planning:
			return

		# If model provided a new plan via plan_update, replace the current plan
		if model_output.plan_update is not None:
			self.state.plan = [PlanItem(text=step_text) for step_text in model_output.plan_update]
			self.state.current_plan_item_index = 0
			self.state.plan_generation_step = self.state.n_steps
			if self.state.plan:
				self.state.plan[0].status = 'current'
			self.logger.info(
				f'📋 Plan {"updated" if self.state.plan_generation_step else "created"} with {len(self.state.plan)} steps'
			)
			return

		# If model provided a step index update, advance the plan
		if model_output.current_plan_item is not None and self.state.plan is not None:
			new_idx = model_output.current_plan_item
			# Clamp to valid range
			new_idx = max(0, min(new_idx, len(self.state.plan) - 1))
			old_idx = self.state.current_plan_item_index

			# Mark steps between old and new as done
			for i in range(old_idx, new_idx):
				if i < len(self.state.plan) and self.state.plan[i].status in ('current', 'pending'):
					self.state.plan[i].status = 'done'

			# Mark the new step as current
			if new_idx < len(self.state.plan):
				self.state.plan[new_idx].status = 'current'

			self.state.current_plan_item_index = new_idx