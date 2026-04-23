async def run_research(topic):
    # Reset state for new research
    st.session_state.collected_facts = []
    st.session_state.research_done = False
    st.session_state.report_result = None

    with tab1:
        message_container = st.container()

    # Create error handling container
    error_container = st.empty()

    # Create a trace for the entire workflow
    with trace("News Research", group_id=st.session_state.conversation_id):
        # Start with the triage agent
        with message_container:
            st.write("🔍 **Triage Agent**: Planning research approach...")

        triage_result = await Runner.run(
            triage_agent,
            f"Research this topic thoroughly: {topic}. This research will be used to create a comprehensive research report."
        )

        # Check if the result is a ResearchPlan object or a string
        if hasattr(triage_result.final_output, 'topic'):
            research_plan = triage_result.final_output
            plan_display = {
                "topic": research_plan.topic,
                "search_queries": research_plan.search_queries,
                "focus_areas": research_plan.focus_areas
            }
        else:
            # Fallback if we don't get the expected output type
            research_plan = {
                "topic": topic,
                "search_queries": ["Researching " + topic],
                "focus_areas": ["General information about " + topic]
            }
            plan_display = research_plan

        with message_container:
            st.write("📋 **Research Plan**:")
            st.json(plan_display)

        # Display facts as they're collected
        fact_placeholder = message_container.empty()

        # Check for new facts periodically
        previous_fact_count = 0
        for i in range(15):  # Check more times to allow for more comprehensive research
            current_facts = len(st.session_state.collected_facts)
            if current_facts > previous_fact_count:
                with fact_placeholder.container():
                    st.write("📚 **Collected Facts**:")
                    for fact in st.session_state.collected_facts:
                        st.info(f"**Fact**: {fact['fact']}\n\n**Source**: {fact['source']}")
                previous_fact_count = current_facts
            await asyncio.sleep(1)

        # Editor Agent phase
        with message_container:
            st.write("📝 **Editor Agent**: Creating comprehensive research report...")

        try:
            report_result = await Runner.run(
                editor_agent,
                triage_result.to_input_list()
            )

            st.session_state.report_result = report_result.final_output

            with message_container:
                st.write("✅ **Research Complete! Report Generated.**")

                # Preview a snippet of the report
                if hasattr(report_result.final_output, 'report'):
                    report_preview = report_result.final_output.report[:300] + "..."
                else:
                    report_preview = str(report_result.final_output)[:300] + "..."

                st.write("📄 **Report Preview**:")
                st.markdown(report_preview)
                st.write("*See the Report tab for the full document.*")

        except Exception as e:
            st.error(f"Error generating report: {str(e)}")
            # Fallback to display raw agent response
            if hasattr(triage_result, 'new_items'):
                messages = [item for item in triage_result.new_items if hasattr(item, 'content')]
                if messages:
                    raw_content = "\n\n".join([str(m.content) for m in messages if m.content])
                    st.session_state.report_result = raw_content

                    with message_container:
                        st.write("⚠️ **Research completed but there was an issue generating the structured report.**")
                        st.write("Raw research results are available in the Report tab.")

    st.session_state.research_done = True