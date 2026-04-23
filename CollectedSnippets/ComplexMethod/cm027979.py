def render_exception_handling(agent, model_choice, temperature, max_turns):
    """Render the exception handling demo"""
    st.header("⚠️ Exception Handling Demo")
    st.markdown("Demonstrates proper exception handling for different SDK error scenarios.")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("🚫 MaxTurns Exception")
        st.caption("Trigger MaxTurnsExceeded exception")

        with st.form("maxturns_form"):
            max_turns_test = st.number_input("Max Turns (set low to trigger)", 1, 5, 2)
            maxturns_input = st.text_area(
                "Your message:", 
                value="Keep asking me questions and I'll keep responding. Let's have a long conversation."
            )
            maxturns_submitted = st.form_submit_button("Test MaxTurns")

            if maxturns_submitted and maxturns_input:
                try:
                    run_config = RunConfig(max_turns=max_turns_test)
                    result = asyncio.run(Runner.run(agent, maxturns_input, run_config=run_config))
                    st.success("✅ Completed without hitting max turns")
                    st.write(f"**Response:** {result.final_output}")

                except MaxTurnsExceeded as e:
                    st.warning(f"⚠️ MaxTurnsExceeded: {e}")
                    st.info("This is expected when max_turns is set too low for complex conversations.")

                except Exception as e:
                    st.error(f"❌ Unexpected error: {e}")

    with col2:
        st.subheader("🔧 General Exception Handling")
        st.caption("Comprehensive exception handling")

        with st.form("exception_form"):
            exception_input = st.text_area("Your message:", value="Tell me about artificial intelligence")
            exception_submitted = st.form_submit_button("Test Exception Handling")

            if exception_submitted and exception_input:
                try:
                    with st.spinner("Processing with full exception handling..."):
                        result = asyncio.run(Runner.run(agent, exception_input))
                        st.success("✅ Successfully processed")
                        st.write(f"**Response:** {result.final_output}")

                except MaxTurnsExceeded as e:
                    st.warning(f"⚠️ Hit maximum turns limit: {e}")
                    st.info("Consider increasing max_turns or simplifying the request.")

                except ModelBehaviorError as e:
                    st.error(f"🤖 Model behavior error: {e}")
                    st.info("The model produced unexpected output. Try rephrasing your request.")

                except UserError as e:
                    st.error(f"👤 User error: {e}")
                    st.info("There's an issue with the request. Please check your input.")

                except AgentsException as e:
                    st.error(f"🔧 SDK error: {e}")
                    st.info("An error occurred within the Agents SDK.")

                except Exception as e:
                    st.error(f"❌ Unexpected error: {e}")
                    st.info("An unexpected error occurred. Please try again.")

    # Exception handling reference
    st.divider()
    st.subheader("📚 Exception Handling Reference")

    exception_info = {
        "MaxTurnsExceeded": "Agent hit the maximum conversation turns limit",
        "ModelBehaviorError": "LLM produced malformed or unexpected output",
        "UserError": "Invalid SDK usage or request parameters", 
        "AgentsException": "Base exception for all SDK-related errors",
        "InputGuardrailTripwireTriggered": "Input validation failed",
        "OutputGuardrailTripwireTriggered": "Output validation failed"
    }

    for exception, description in exception_info.items():
        st.write(f"**{exception}**: {description}")