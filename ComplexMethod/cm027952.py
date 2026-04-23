def validate_action(self, agent_id: str, action: str, delegation_id: Optional[str] = None) -> bool:
        """Validate if an agent can perform an action under their delegation"""

        if delegation_id:
            delegation = self.delegations.get(delegation_id)
            if not delegation:
                return False
            if not delegation.is_valid():
                return False
            if delegation.child_agent != agent_id:
                return False
            return delegation.scope.allows_action(action)

        # Check if agent has any valid delegation allowing this action
        for del_id in self.agent_delegations.get(agent_id, []):
            delegation = self.delegations.get(del_id)
            if delegation and delegation.is_valid() and delegation.scope.allows_action(action):
                return True

        return False