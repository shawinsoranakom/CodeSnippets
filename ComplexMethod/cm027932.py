def main() -> None:
    st.set_page_config(page_title="Trust-Gated Agent Team", page_icon="🛡️", layout="wide")
    st.title("🛡️ Trust-Gated Multi-Agent Research Team")
    st.caption(
        "Every agent must pass a trust check before participating. "
        "Every action is recorded in a hash-chained audit trail."
    )

    # Registry and audit trail are rebuilt each run (Streamlit re-executes
    # main() on every widget interaction). This is intentional for the demo —
    # in production you would persist these in st.session_state.
    registry = _init_registry()
    audit = AuditTrail()

    with st.sidebar:
        openai_key, threshold, selected_ids = _render_sidebar(registry)

    query = st.text_input(
        "🔎 Research topic",
        placeholder="e.g., How are AI agents being used in supply chain optimization?",
    )

    if not st.button("🚀 Run Trust-Gated Pipeline", type="primary"):
        st.markdown("---")
        st.markdown(
            "### How It Works\n\n"
            "1. Each agent is checked against the trust threshold\n"
            "2. Agents below the threshold are blocked from the pipeline\n"
            "3. Verified agents run in sequence (Researcher → Analyst → Writer)\n"
            "4. Every action is recorded in a SHA-256 hash chain\n"
            "5. The audit trail is exportable and independently verifiable"
        )
        return

    if not openai_key:
        st.warning("Enter your OpenAI API key in the sidebar.")
        return
    if not query or not query.strip():
        st.warning("Enter a research topic.")
        return
    if len(query) > 2000:
        st.warning("Topic too long (max 2000 chars).")
        return

    client = OpenAI(api_key=openai_key)
    verified, blocked = _run_trust_verification(registry, audit, selected_ids, threshold)

    st.divider()
    if blocked:
        st.warning(
            f"⚠️ {len(blocked)} agent(s) blocked: "
            + ", ".join(f"{v.agent.name} (score {v.agent.trust_score})" for v in blocked)
        )
    if not verified:
        st.error("❌ No agents passed. Lower the threshold or change agent selection.")
        _render_audit(audit)
        return

    st.info(f"✅ {len(verified)}/{len(verified) + len(blocked)} agents verified. Running pipeline.")
    _run_research_pipeline(client, audit, verified, query)

    st.divider()
    st.header("Pipeline Summary 📋")
    cols = st.columns(4)
    cols[0].metric("Verified", f"{len(verified)}/{len(verified) + len(blocked)}")
    cols[1].metric("Blocked", len(blocked))
    cols[2].metric("Threshold", f"{threshold}/100")
    cols[3].metric("Audit Entries", len(audit.entries))

    _render_audit(audit)