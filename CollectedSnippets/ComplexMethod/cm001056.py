async def _execute(
        self,
        user_id: str | None,
        session: ChatSession,
        *,
        name: str = "",
        content: str = "",
        source_description: str = "Conversation memory",
        source_kind: str = "user_asserted",
        scope: str = "real:global",
        memory_kind: str = "fact",
        rule: dict | None = None,
        procedure: dict | None = None,
        **kwargs,
    ) -> ToolResponseBase:
        if not user_id:
            return ErrorResponse(
                message="Authentication required to store memories.",
                session_id=session.session_id,
            )

        if not await is_enabled_for_user(user_id):
            return ErrorResponse(
                message="Memory features are not enabled for your account.",
                session_id=session.session_id,
            )

        if not name or not content:
            return ErrorResponse(
                message="Both 'name' and 'content' are required.",
                session_id=session.session_id,
            )

        rule_model = None
        if rule and memory_kind == "rule":
            try:
                rule_model = RuleMemory(**rule)
            except Exception:
                logger.warning("Invalid rule data, storing as plain fact")
                memory_kind = "fact"

        procedure_model = None
        if procedure and memory_kind == "procedure":
            try:
                steps = [ProcedureStep(**s) for s in procedure.get("steps", [])]
                procedure_model = ProcedureMemory(
                    description=procedure.get("description", content),
                    steps=steps,
                )
            except Exception:
                logger.warning("Invalid procedure data, storing as plain fact")
                memory_kind = "fact"

        try:
            resolved_source = SourceKind(source_kind)
        except ValueError:
            resolved_source = SourceKind.user_asserted
        try:
            resolved_kind = MemoryKind(memory_kind)
        except ValueError:
            resolved_kind = MemoryKind.fact

        envelope = MemoryEnvelope(
            content=content,
            source_kind=resolved_source,
            scope=scope,
            memory_kind=resolved_kind,
            status=MemoryStatus.active,
            provenance=session.session_id,
            rule=rule_model,
            procedure=procedure_model,
        )

        queued = await enqueue_episode(
            user_id,
            session.session_id,
            name=name,
            episode_body=envelope.model_dump_json(),
            source_description=source_description,
            is_json=True,
        )

        if not queued:
            return ErrorResponse(
                message="Memory queue is full — please try again shortly.",
                session_id=session.session_id,
            )

        return MemoryStoreResponse(
            message=f"Memory '{name}' queued for storage.",
            session_id=session.session_id,
            memory_name=name,
        )