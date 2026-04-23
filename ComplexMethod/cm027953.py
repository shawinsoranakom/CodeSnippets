def evaluate(
        self,
        agent_id: str,
        action: str,
        roles: List[str],
        delegation_id: Optional[str] = None
    ) -> tuple[bool, str]:
        """Evaluate if an action is allowed"""

        # Check trust level
        trust = self.trust_engine.get(agent_id)
        if not trust:
            return False, "Agent has no trust score"

        if trust.level == TrustLevel.SUSPENDED:
            return False, "Agent is suspended"

        # Check role-based policies
        for role in roles:
            policy = self.role_policies.get(role, {})

            # Check base trust requirement
            min_trust = policy.get("base_trust_required", 0)
            if trust.score < min_trust:
                return False, f"Trust score {trust.score} below minimum {min_trust} for role {role}"

            # Check denied actions
            if action in policy.get("denied_actions", []):
                return False, f"Action '{action}' denied for role {role}"

            # Check allowed actions (if specified, action must be in list)
            allowed = policy.get("allowed_actions", [])
            if allowed and action not in allowed:
                return False, f"Action '{action}' not in allowed list for role {role}"

        # Check delegation
        if delegation_id:
            if not self.delegation_manager.validate_action(agent_id, action, delegation_id):
                return False, f"Action '{action}' not allowed under delegation {delegation_id}"

        # Require approval for restricted agents
        if trust.level == TrustLevel.RESTRICTED:
            return False, "Agent is restricted - requires human approval"

        return True, "Action allowed"