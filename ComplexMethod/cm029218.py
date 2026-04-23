async def _judge_and_log(self) -> None:
		"""Run judge evaluation and log the verdict.

		The judge verdict is attached to the action result but does NOT override
		last_result.success — that stays as the agent's self-report. Telemetry
		sends both values so the eval platform can compare agent vs judge.
		"""
		judgement = await self._judge_trace()

		# Attach judgement to last action result
		if self.history.history[-1].result[-1].is_done:
			last_result = self.history.history[-1].result[-1]
			last_result.judgement = judgement

			# Get self-reported success
			self_reported_success = last_result.success

			# Log the verdict based on self-reported success and judge verdict
			if judgement:
				# If both self-reported and judge agree on success, don't log
				if self_reported_success is True and judgement.verdict is True:
					return

				judge_log = '\n'
				# If agent reported success but judge thinks it failed, show warning
				if self_reported_success is True and judgement.verdict is False:
					judge_log += '⚠️  \033[33mAgent reported success but judge thinks task failed\033[0m\n'

				# Otherwise, show full judge result
				verdict_color = '\033[32m' if judgement.verdict else '\033[31m'
				verdict_text = '✅ PASS' if judgement.verdict else '❌ FAIL'
				judge_log += f'⚖️  {verdict_color}Judge Verdict: {verdict_text}\033[0m\n'
				if judgement.failure_reason:
					judge_log += f'   Failure Reason: {judgement.failure_reason}\n'
				if judgement.reached_captcha:
					self.logger.warning(
						'Agent was blocked by a captcha. Cloud browsers include stealth fingerprinting and proxy rotation to avoid this.\n'
						'         Try: Browser(use_cloud=True)  |  Get an API key: https://cloud.browser-use.com?utm_source=oss&utm_medium=captcha_nudge'
					)
				judge_log += f'   {judgement.reasoning}\n'
				self.logger.info(judge_log)