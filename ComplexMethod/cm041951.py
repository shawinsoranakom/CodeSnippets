def main():
    if "optimization_results" not in st.session_state:
        st.session_state.optimization_results = []

    st.markdown(
        """
        <div style="background-color: #f0f2f6; padding: 20px; border-radius: 10px; margin-bottom: 25px">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px">
                <h1 style="margin: 0;">SPO | Self-Supervised Prompt Optimization 🤖</h1>
            </div>
            <div style="display: flex; gap: 20px; align-items: center">
                <a href="https://arxiv.org/pdf/2502.06855" target="_blank" style="text-decoration: none;">
                    <img src="https://img.shields.io/badge/Paper-PDF-red.svg" alt="Paper">
                </a>
                <a href="https://github.com/geekan/MetaGPT/blob/main/examples/spo/README.md" target="_blank" style="text-decoration: none;">
                    <img src="https://img.shields.io/badge/GitHub-Repository-blue.svg" alt="GitHub">
                </a>
                <span style="color: #666;">A framework for self-supervised prompt optimization</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Sidebar for configurations
    with st.sidebar:
        st.header("Configuration")

        # Template Selection/Creation
        settings_path = Path("metagpt/ext/spo/settings")
        existing_templates = [f.stem for f in settings_path.glob("*.yaml")]

        template_mode = st.radio("Template Mode", ["Use Existing", "Create New"])

        if template_mode == "Use Existing":
            template_name = st.selectbox("Select Template", existing_templates)
        else:
            template_name = st.text_input("New Template Name")
            if template_name and not template_name.endswith(".yaml"):
                template_name = f"{template_name}"

        # LLM Settings
        st.subheader("LLM Settings")
        opt_model = st.selectbox(
            "Optimization Model", ["claude-3-5-sonnet-20240620", "gpt-4o", "gpt-4o-mini", "deepseek-chat"], index=0
        )
        opt_temp = st.slider("Optimization Temperature", 0.0, 1.0, 0.7)

        eval_model = st.selectbox(
            "Evaluation Model", ["gpt-4o-mini", "claude-3-5-sonnet-20240620", "gpt-4o", "deepseek-chat"], index=0
        )
        eval_temp = st.slider("Evaluation Temperature", 0.0, 1.0, 0.3)

        exec_model = st.selectbox(
            "Execution Model", ["gpt-4o-mini", "claude-3-5-sonnet-20240620", "gpt-4o", "deepseek-chat"], index=0
        )
        exec_temp = st.slider("Execution Temperature", 0.0, 1.0, 0.0)

        # Optimizer Settings
        st.subheader("Optimizer Settings")
        initial_round = st.number_input("Initial Round", 1, 100, 1)
        max_rounds = st.number_input("Maximum Rounds", 1, 100, 10)

    # Main content area
    st.header("Template Configuration")

    if template_name:
        template_path = settings_path / f"{template_name}.yaml"
        template_data = load_yaml_template(template_path)

        if "current_template" not in st.session_state or st.session_state.current_template != template_name:
            st.session_state.current_template = template_name
            st.session_state.qas = template_data.get("qa", [])

        # Edit template sections
        prompt = st.text_area("Prompt", template_data.get("prompt", ""), height=100)
        requirements = st.text_area("Requirements", template_data.get("requirements", ""), height=100)

        # qa section
        st.subheader("Q&A Examples")

        # Add new qa button
        if st.button("Add New Q&A"):
            st.session_state.qas.append({"question": "", "answer": ""})

        # Edit qas
        new_qas = []
        for i in range(len(st.session_state.qas)):
            st.markdown(f"**QA #{i + 1}**")
            col1, col2, col3 = st.columns([45, 45, 10])

            with col1:
                question = st.text_area(
                    f"Question {i + 1}", st.session_state.qas[i].get("question", ""), key=f"q_{i}", height=100
                )
            with col2:
                answer = st.text_area(
                    f"Answer {i + 1}", st.session_state.qas[i].get("answer", ""), key=f"a_{i}", height=100
                )
            with col3:
                if st.button("🗑️", key=f"delete_{i}"):
                    st.session_state.qas.pop(i)
                    st.rerun()

            new_qas.append({"question": question, "answer": answer})

        # Save template button
        if st.button("Save Template"):
            new_template_data = {"prompt": prompt, "requirements": requirements, "count": None, "qa": new_qas}

            save_yaml_template(template_path, new_template_data)

            st.session_state.qas = new_qas
            st.success(f"Template saved to {template_path}")

        st.subheader("Current Template Preview")
        preview_data = {"qa": new_qas, "requirements": requirements, "prompt": prompt}
        st.code(yaml.dump(preview_data, allow_unicode=True), language="yaml")

        st.subheader("Optimization Logs")
        log_container = st.empty()

        class StreamlitSink:
            def write(self, message):
                current_logs = st.session_state.get("logs", [])
                current_logs.append(message.strip())
                st.session_state.logs = current_logs

                log_container.code("\n".join(current_logs), language="plaintext")

        streamlit_sink = StreamlitSink()
        _logger.remove()

        def prompt_optimizer_filter(record):
            return "optimizer" in record["name"].lower()

        _logger.add(
            streamlit_sink.write,
            format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} - {message}",
            filter=prompt_optimizer_filter,
        )
        _logger.add(METAGPT_ROOT / "logs/{time:YYYYMMDD}.txt", level="DEBUG")

        # Start optimization button
        if st.button("Start Optimization"):
            try:
                # Initialize LLM
                SPO_LLM.initialize(
                    optimize_kwargs={"model": opt_model, "temperature": opt_temp},
                    evaluate_kwargs={"model": eval_model, "temperature": eval_temp},
                    execute_kwargs={"model": exec_model, "temperature": exec_temp},
                )

                # Create optimizer instance
                optimizer = PromptOptimizer(
                    optimized_path="workspace",
                    initial_round=initial_round,
                    max_rounds=max_rounds,
                    template=f"{template_name}.yaml",
                    name=template_name,
                )

                # Run optimization with progress bar
                with st.spinner("Optimizing prompts..."):
                    optimizer.optimize()

                st.success("Optimization completed!")

                st.header("Optimization Results")

                prompt_path = optimizer.root_path / "prompts"
                result_data = optimizer.data_utils.load_results(prompt_path)

                st.session_state.optimization_results = result_data

            except Exception as e:
                st.error(f"An error occurred: {str(e)}")
                _logger.error(f"Error during optimization: {str(e)}")

        if st.session_state.optimization_results:
            st.header("Optimization Results")
            display_optimization_results(st.session_state.optimization_results)

        st.markdown("---")
        st.subheader("Test Optimized Prompt")
        col1, col2 = st.columns(2)

        with col1:
            test_prompt = st.text_area("Optimized Prompt", value="", height=200, key="test_prompt")

        with col2:
            test_question = st.text_area("Your Question", value="", height=200, key="test_question")

        if st.button("Test Prompt"):
            if test_prompt and test_question:
                try:
                    with st.spinner("Generating response..."):
                        SPO_LLM.initialize(
                            optimize_kwargs={"model": opt_model, "temperature": opt_temp},
                            evaluate_kwargs={"model": eval_model, "temperature": eval_temp},
                            execute_kwargs={"model": exec_model, "temperature": exec_temp},
                        )

                        llm = SPO_LLM.get_instance()
                        messages = [{"role": "user", "content": f"{test_prompt}\n\n{test_question}"}]

                        async def get_response():
                            return await llm.responser(request_type=RequestType.EXECUTE, messages=messages)

                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        try:
                            response = loop.run_until_complete(get_response())
                        finally:
                            loop.close()

                        st.subheader("Response:")
                        st.markdown(response)

                except Exception as e:
                    st.error(f"Error generating response: {str(e)}")
            else:
                st.warning("Please enter both prompt and question.")