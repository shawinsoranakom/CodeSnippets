def render_recommendations(result: Dict[str, Any], profile: Dict[str, Any]) -> None:
    coverage_currency = result.get("coverage_currency", currency)
    coverage_amount = safe_number(result.get("coverage_amount", 0))

    st.subheader("Recommended Coverage")
    st.metric(
        label="Total Coverage Needed",
        value=format_currency(coverage_amount, coverage_currency),
    )

    assumptions = result.get("assumptions", {})
    real_rate = parse_percentage(assumptions.get("real_discount_rate", "2%"))
    local_breakdown = compute_local_breakdown(profile, real_rate)

    st.subheader("Calculation Inputs")
    st.table(
        {
            "Input": [
                "Annual income",
                "Income replacement horizon",
                "Total debt",
                "Liquid assets",
                "Existing life cover",
                "Real discount rate",
            ],
            "Value": [
                format_currency(local_breakdown["income"], coverage_currency),
                f"{local_breakdown['years']} years",
                format_currency(local_breakdown["debt"], coverage_currency),
                format_currency(safe_number(profile.get("available_savings")), coverage_currency),
                format_currency(safe_number(profile.get("existing_life_insurance")), coverage_currency),
                f"{real_rate * 100:.2f}%",
            ],
        }
    )

    st.subheader("Step-by-step Coverage Math")
    step_rows = [
        ("Annuity factor", f"{local_breakdown['annuity_factor']:.3f}"),
        ("Discounted income replacement", format_currency(local_breakdown["discounted_income"], coverage_currency)),
        ("+ Outstanding debt", format_currency(local_breakdown["debt"], coverage_currency)),
        ("- Assets & existing cover", format_currency(local_breakdown["assets_offset"], coverage_currency)),
        ("= Formula estimate", format_currency(local_breakdown["recommended"], coverage_currency)),
    ]
    step_rows.append(("= Agent recommendation", format_currency(coverage_amount, coverage_currency)))

    st.table({"Step": [s for s, _ in step_rows], "Amount": [a for _, a in step_rows]})

    breakdown = result.get("breakdown", {})
    with st.expander("How this number was calculated", expanded=True):
        st.markdown(
            f"- Income replacement value: {format_currency(safe_number(breakdown.get('income_replacement')), coverage_currency)}"
        )
        st.markdown(
            f"- Debt obligations: {format_currency(safe_number(breakdown.get('debt_obligations')), coverage_currency)}"
        )
        assets_offset = safe_number(breakdown.get("assets_offset"))
        st.markdown(
            f"- Assets & existing cover offset: {format_currency(assets_offset, coverage_currency)}"
        )
        methodology = breakdown.get("methodology")
        if methodology:
            st.caption(methodology)

    recommendations = result.get("recommendations", [])
    if recommendations:
        st.subheader("Top Term Life Options")
        for idx, option in enumerate(recommendations, start=1):
            with st.container():
                name = option.get("name", "Unnamed Product")
                summary = option.get("summary", "No summary provided.")
                st.markdown(f"**{idx}. {name}** — {summary}")
                link = option.get("link")
                if link:
                    st.markdown(f"[View details]({link})")
                source = option.get("source")
                if source:
                    st.caption(f"Source: {source}")
                st.markdown("---")

    with st.expander("Model assumptions"):
        st.write(
            {
                "Income replacement years": assumptions.get(
                    "income_replacement_years", income_replacement_years
                ),
                "Real discount rate": assumptions.get("real_discount_rate", "2%"),
                "Notes": assumptions.get("additional_notes", ""),
            }
        )

    if result.get("research_notes"):
        st.caption(result["research_notes"])
    if result.get("timestamp"):
        st.caption(f"Generated: {result['timestamp']}")

    with st.expander("Agent response JSON"):
        st.json(result)