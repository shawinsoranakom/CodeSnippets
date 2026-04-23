def create_delegation(
        self,
        parent_agent: str,
        child_agent: str,
        scope: DelegationScope,
        task_description: str,
        time_limit_minutes: Optional[int] = None,
        parent_delegation_id: Optional[str] = None
    ) -> Optional[Delegation]:
        """Create a new delegation from parent to child agent"""

        # Verify both agents exist
        if not self.identity_registry.get(parent_agent):
            logger.error(f"Parent agent not found: {parent_agent}")
            return None
        if not self.identity_registry.get(child_agent):
            logger.error(f"Child agent not found: {child_agent}")
            return None

        # Check parent's trust level
        parent_trust = self.trust_engine.get(parent_agent)
        if parent_trust and parent_trust.level == TrustLevel.SUSPENDED:
            logger.error(f"Suspended agent cannot delegate: {parent_agent}")
            return None

        # If this is a sub-delegation, narrow the scope
        if parent_delegation_id:
            parent_del = self.delegations.get(parent_delegation_id)
            if not parent_del or not parent_del.is_valid():
                logger.error(f"Invalid parent delegation: {parent_delegation_id}")
                return None
            if parent_del.scope.max_sub_delegations <= 0:
                logger.error(f"No sub-delegations allowed under: {parent_delegation_id}")
                return None
            scope = parent_del.scope.narrow(scope)

        # Create delegation
        delegation_id = f"del-{secrets.token_hex(8)}"
        time_limit = time_limit_minutes or scope.time_limit_minutes

        delegation = Delegation(
            delegation_id=delegation_id,
            parent_agent=parent_agent,
            child_agent=child_agent,
            scope=scope,
            task_description=task_description,
            created_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(minutes=time_limit),
            signature=self._sign_delegation(parent_agent, delegation_id),
            parent_delegation_id=parent_delegation_id
        )

        self.delegations[delegation_id] = delegation
        self.agent_delegations[child_agent].append(delegation_id)

        logger.info(f"Created delegation: {parent_agent} → {child_agent} ({delegation_id})")
        return delegation