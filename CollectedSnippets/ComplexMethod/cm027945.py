def run_pipeline():
    """
    Execute the full signal intelligence pipeline.

    Pipeline stages:
    1. Signal Collection — Aggregate from sources (utility, no LLM)
    2. Normalization    — Deduplicate and normalize (utility, no LLM)
    3. Relevance Score  — Rate signals 0-100 (agent, gpt-4.1-mini)
    4. Risk Assessment  — Identify risks (agent, gpt-4.1-mini)
    5. Synthesis        — Produce digest (agent, gpt-4.1)
    """
    print("=" * 60)
    print("🧠 DevPulseAI — Signal Intelligence Pipeline")
    print("=" * 60)

    # Check for API key
    if not os.environ.get("OPENAI_API_KEY"):
        print("\n⚠️  Warning: OPENAI_API_KEY not set.")
        print("   Agents will use fallback heuristics.\n")

    # Stage 1: Collect raw signals from adapters
    raw_signals = collect_signals()

    # Stage 2: Normalize and deduplicate (utility — no LLM)
    collector = SignalCollector()
    print("\n🔄 [2/4] Normalizing Signals...")
    normalized = collector.collect(raw_signals)
    print(f"  ✓ {collector.summarize_collection(normalized)}")

    # Stage 3: Score for relevance (agent — gpt-4.1-mini)
    relevance = RelevanceAgent()
    print("\n📊 [3/4] Scoring Relevance...")
    scored = relevance.score_batch(normalized)
    high_relevance = sum(
        1 for s in scored if s.get("relevance", {}).get("score", 0) >= 70
    )
    print(f"  ✓ {high_relevance}/{len(scored)} signals rated high-relevance")

    # Stage 4: Assess risks (agent — gpt-4.1-mini)
    risk = RiskAgent()
    print("\n⚠️  [4/4] Assessing Risks...")
    assessed = risk.assess_batch(scored)
    critical = sum(
        1
        for s in assessed
        if s.get("risk", {}).get("risk_level") in ["HIGH", "CRITICAL"]
    )
    print(f"  ✓ {critical}/{len(assessed)} signals with elevated risk")

    # Stage 5: Synthesize digest (agent — gpt-4.1)
    synthesis = SynthesisAgent()
    print("\n📋 Generating Intelligence Digest...")
    digest = synthesis.synthesize(assessed)

    # Output results
    print("\n" + "=" * 60)
    print("📄 INTELLIGENCE DIGEST")
    print("=" * 60)
    print(f"\n🕐 Generated: {digest['generated_at']}")
    print(f"📦 Total Signals: {digest['total_signals']}")
    print(f"\n📝 Summary: {digest['executive_summary']}")

    print("\n🎯 Top Priority Signals:")
    for i, signal in enumerate(digest.get("priority_signals", [])[:3], 1):
        score = signal.get("relevance", {}).get("score", "?")
        risk_level = signal.get("risk", {}).get("risk_level", "?")
        print(f"   {i}. [{signal['source']}] {signal['title'][:50]}...")
        print(f"      Relevance: {score} | Risk: {risk_level}")

    print("\n💡 Recommendations:")
    for rec in digest.get("recommendations", []):
        print(f"   • {rec}")

    print("\n" + "=" * 60)
    print("✅ Pipeline completed successfully!")
    print("=" * 60)

    return digest