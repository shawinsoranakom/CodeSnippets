def main():
    print("🛡️ AI Agent Governance Demo")
    print("=" * 40)

    # Define policy configuration
    policy_yaml = """
policies:
  filesystem:
    allowed_paths: 
      - /workspace
      - /tmp
    denied_paths:
      - /etc
      - /home
      - ~/.ssh

  network:
    allowed_domains:
      - api.openai.com
      - api.github.com
    block_all_others: true

  execution:
    max_actions_per_minute: 60
    require_approval_for:
      - delete_file
      - execute_shell
"""

    print("\n📋 Loading policy configuration...")
    policy_engine = PolicyEngine.from_yaml(policy_yaml)
    print("✅ Policy engine initialized with rules:")
    for rule in policy_engine.rules:
        print(f"   - {rule.name}")

    # Create governed tools
    tools = create_governed_tools(policy_engine)

    # Demo: Test various actions
    print("\n" + "=" * 40)
    print("📝 Testing Governance Layer")
    print("=" * 40)

    test_cases = [
        ("read_file", {"path": "/etc/passwd"}),
        ("write_file", {"path": "/workspace/report.md", "content": "# Analysis Report\n"}),
        ("web_request", {"url": "https://api.github.com/users"}),
        ("web_request", {"url": "https://unknown-site.com/api"}),
        ("read_file", {"path": "/workspace/data.txt"}),
    ]

    for tool_name, kwargs in test_cases:
        print(f"\n🤖 Testing: {tool_name}({kwargs})")
        try:
            # We need to create a temp file for the read test
            if tool_name == "read_file" and kwargs["path"] == "/workspace/data.txt":
                os.makedirs("/workspace", exist_ok=True)
                with open("/workspace/data.txt", "w") as f:
                    f.write("Test data")

            result = tools[tool_name](**kwargs)
            print(f"   Result: {result}")
        except PolicyViolation as e:
            print(f"   {e}")
        except Exception as e:
            print(f"   Error: {e}")

    # Print audit log
    print("\n" + "=" * 40)
    print("📊 Audit Log")
    print("=" * 40)
    for entry in policy_engine.get_audit_log():
        print(f"   {entry['decision'].upper():8} | {entry['action']:15} | {entry['reason'][:50]}")

    # Demo with LLM agent (optional - requires API key)
    if os.getenv("OPENAI_API_KEY"):
        print("\n" + "=" * 40)
        print("🤖 LLM Agent Demo (with governance)")
        print("=" * 40)

        agent = GovernedAgent(policy_engine)

        demo_requests = [
            "Read the contents of /etc/passwd",
            "Write a summary to /workspace/summary.md", 
            "Make a request to api.github.com to get user info"
        ]

        for request in demo_requests:
            print(f"\n👤 User: {request}")
            result = agent.run(request)
            print(f"📤 Result: {result}")
    else:
        print("\n💡 Set OPENAI_API_KEY to run the full LLM agent demo")

    print("\n✅ Demo complete!")