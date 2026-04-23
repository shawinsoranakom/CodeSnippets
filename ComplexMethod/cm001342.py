def _parse_critique(
        self, critic_id: str, target_id: str, result: str
    ) -> Optional[AgentCritique]:
        """Parse a critique from sub-agent output."""
        try:
            strengths = re.findall(
                r"STRENGTHS?:\s*(.+?)(?=WEAKNESSES?:|$)",
                result,
                re.DOTALL | re.IGNORECASE,
            )
            weaknesses = re.findall(
                r"WEAKNESSES?:\s*(.+?)(?=SUGGESTIONS?:|$)",
                result,
                re.DOTALL | re.IGNORECASE,
            )
            suggestions = re.findall(
                r"SUGGESTIONS?:\s*(.+?)(?=SCORE:|$)", result, re.DOTALL | re.IGNORECASE
            )
            score_match = re.search(r"SCORE:\s*([\d.]+)", result)

            return AgentCritique(
                critic_id=critic_id,
                target_agent_id=target_id,
                strengths=[s.strip() for s in strengths] if strengths else [],
                weaknesses=[w.strip() for w in weaknesses] if weaknesses else [],
                suggestions=[s.strip() for s in suggestions] if suggestions else [],
                score=float(score_match.group(1)) if score_match else 0.5,
            )

        except Exception as e:
            self.logger.warning(f"Failed to parse critique: {e}")
            return None