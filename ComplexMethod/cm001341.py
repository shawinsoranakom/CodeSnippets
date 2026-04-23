async def run_critique_phase(self, task: str) -> list[AgentCritique]:
        """Run the critique phase with sub-agents."""
        if not self.can_spawn_sub_agent() or not self.debate_state.proposals:
            return []

        critique_tasks = []
        for i, proposal in enumerate(self.debate_state.proposals):
            # Each other debater critiques this proposal
            for j in range(self.config.num_debaters):
                if j == i:
                    continue  # Don't critique own proposal

                sub_task = self.config.critique_instruction.format(
                    task=task,
                    action=proposal.action_name,
                    arguments=json.dumps(proposal.action_args),
                    reasoning=proposal.reasoning,
                )
                critique_tasks.append((f"critic-{j + 1}", proposal.agent_id, sub_task))

        try:
            # Run critiques (limit parallelism)
            critiques = []
            for critic_id, target_id, sub_task in critique_tasks:
                result = await self.spawn_and_run(
                    sub_task,
                    strategy="one_shot",
                    max_cycles=5,
                )
                if result:
                    critique = self._parse_critique(critic_id, target_id, str(result))
                    if critique:
                        critiques.append(critique)

            self.debate_state.critiques = critiques
            self.current_round += 1

            if self.current_round >= self.config.num_rounds:
                self.phase = DebatePhase.CONSENSUS
            else:
                self.phase = DebatePhase.PROPOSAL  # Another round

            return critiques

        except Exception as e:
            self.logger.error(f"Critique phase failed: {e}")
            return []