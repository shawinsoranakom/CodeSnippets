def main():
    print("🤝 Multi-Agent Trust Layer Demo")
    print("=" * 40)

    # Initialize trust layer
    trust_layer = TrustLayer()

    # Add role policies
    trust_layer.policy_engine.add_role_policy("researcher", {
        "base_trust_required": 500,
        "allowed_actions": ["web_search", "read_document", "summarize", "analyze"],
        "denied_actions": ["execute_code", "send_email", "delete_file"]
    })

    trust_layer.policy_engine.add_role_policy("writer", {
        "base_trust_required": 600,
        "allowed_actions": ["write_document", "edit_document", "summarize"],
        "denied_actions": ["execute_code", "web_search"]
    })

    trust_layer.policy_engine.add_role_policy("orchestrator", {
        "base_trust_required": 800,
        "allowed_actions": [],  # Can do anything not explicitly denied
        "denied_actions": ["delete_system_files"]
    })

    # Register agents
    print("\n📋 Registering agents...")

    trust_layer.register_agent(
        agent_id="orchestrator-001",
        human_sponsor="alice@company.com",
        organization="Acme Corp",
        roles=["orchestrator"],
        initial_trust=900
    )
    print("✅ Registered: orchestrator-001 (Sponsor: alice@company.com)")

    trust_layer.register_agent(
        agent_id="researcher-002",
        human_sponsor="bob@company.com",
        organization="Acme Corp",
        roles=["researcher"],
        initial_trust=750
    )
    print("✅ Registered: researcher-002 (Sponsor: bob@company.com)")

    trust_layer.register_agent(
        agent_id="writer-003",
        human_sponsor="carol@company.com",
        organization="Acme Corp",
        roles=["writer"],
        initial_trust=700
    )
    print("✅ Registered: writer-003 (Sponsor: carol@company.com)")

    # Create delegation chain
    print("\n🔐 Creating delegation chain...")

    delegation_id = trust_layer.create_delegation(
        from_agent="orchestrator-001",
        to_agent="researcher-002",
        scope={
            "allowed_actions": ["web_search", "summarize"],
            "allowed_domains": ["arxiv.org", "github.com"],
            "max_tokens": 50000
        },
        task_description="Research recent papers on AI safety",
        time_limit_minutes=30
    )
    print(f"✅ Delegation: orchestrator-001 → researcher-002")
    print(f"   ID: {delegation_id}")
    print(f"   Scope: web_search, summarize")
    print(f"   Time Limit: 30 minutes")

    # Create governed agents
    researcher = GovernedAgent("researcher-002", trust_layer)
    researcher.current_delegation = delegation_id

    writer = GovernedAgent("writer-003", trust_layer)

    # Test actions
    print("\n" + "=" * 40)
    print("🧪 Testing Agent Actions")
    print("=" * 40)

    # Test 1: Allowed action within delegation
    print("\n🤖 researcher-002: web_search (within scope)")
    result = researcher.execute("web_search", {"query": "AI safety papers 2024"})
    print(f"   Result: {'✅ ALLOWED' if result['success'] else '❌ DENIED'}")
    print(f"   Trust Score: {result['trust_score']}")

    # Test 2: Denied action outside delegation
    print("\n🤖 researcher-002: send_email (outside scope)")
    result = researcher.execute("send_email", {"to": "test@example.com"})
    print(f"   Result: {'✅ ALLOWED' if result['success'] else '❌ DENIED'}")
    if not result['success']:
        print(f"   Reason: {result['error']}")
    print(f"   Trust Score: {result['trust_score']}")

    # Test 3: Writer tries action not in role
    print("\n🤖 writer-003: web_search (not in role)")
    result = writer.execute("web_search", {"query": "test"})
    print(f"   Result: {'✅ ALLOWED' if result['success'] else '❌ DENIED'}")
    if not result['success']:
        print(f"   Reason: {result['error']}")
    print(f"   Trust Score: {result['trust_score']}")

    # Test 4: Writer does allowed action
    print("\n🤖 writer-003: write_document (in role)")
    result = writer.execute("write_document", {"content": "Report draft"})
    print(f"   Result: {'✅ ALLOWED' if result['success'] else '❌ DENIED'}")
    print(f"   Trust Score: {result['trust_score']}")

    # Show final trust scores
    print("\n" + "=" * 40)
    print("📊 Final Trust Scores")
    print("=" * 40)

    for agent_id in ["orchestrator-001", "researcher-002", "writer-003"]:
        score = trust_layer.get_trust_score(agent_id)
        level = trust_layer.get_trust_level(agent_id)
        print(f"   {agent_id}: {score} ({level.value})")

    # Show audit log
    print("\n" + "=" * 40)
    print("📋 Audit Log")
    print("=" * 40)

    for entry in trust_layer.get_audit_log():
        status = "✅" if entry["result"] == "allowed" else "❌"
        print(f"   {status} {entry['agent_id']}: {entry['action']} - {entry['result']}")

    print("\n✅ Demo complete!")