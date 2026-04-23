async def call_agent(
        self, current_input: str, tools: list[Tool], history_messages: list[Message], llm
    ) -> AsyncIterator[dict[str, Any]]:
        """Execute the Cuga agent with the given input and tools.

        This method initializes and runs the Cuga agent, processing the input through
        the agent's workflow and yielding events for real-time monitoring.

        Args:
            current_input: The user input to process
            tools: List of available tools for the agent
            history_messages: Previous conversation history
            llm: The language model instance to use

        Yields:
            dict: Agent events including tool usage, thinking, and final results

        Raises:
            ValueError: If there's an error in agent initialization
            TypeError: If there's a type error in processing
            RuntimeError: If there's a runtime error during execution
            ConnectionError: If there's a connection issue
        """
        yield {
            "event": "on_chain_start",
            "run_id": str(uuid.uuid4()),
            "name": "CUGA_initializing",
            "data": {"input": {"input": current_input, "chat_history": []}},
        }
        logger.debug(f"[CUGA] LLM MODEL TYPE: {type(llm)}")
        if current_input:
            # Import settings first
            from cuga.config import settings

            # Use Dynaconf's set() method to update settings dynamically
            # This properly updates the settings object without corruption
            logger.debug("[CUGA] Updating CUGA settings via Dynaconf set() method")

            settings.advanced_features.registry = False
            settings.advanced_features.lite_mode = self.lite_mode
            settings.advanced_features.lite_mode_tool_threshold = self.lite_mode_tool_threshold
            settings.advanced_features.decomposition_strategy = self.decomposition_strategy

            if self.browser_enabled:
                logger.debug("[CUGA] browser_enabled is true, setting mode to hybrid")
                settings.advanced_features.mode = "hybrid"
                settings.advanced_features.use_vision = False
            else:
                logger.debug("[CUGA] browser_enabled is false, setting mode to api")
                settings.advanced_features.mode = "api"

            from cuga.backend.activity_tracker.tracker import ActivityTracker
            from cuga.backend.cuga_graph.utils.agent_loop import StreamEvent
            from cuga.backend.cuga_graph.utils.controller import (
                AgentRunner as CugaAgent,
            )
            from cuga.backend.cuga_graph.utils.controller import (
                ExperimentResult as AgentResult,
            )
            from cuga.backend.llm.models import LLMManager
            from cuga.configurations.instructions_manager import InstructionsManager

            # Reset var_manager if this is the first message in history
            logger.debug(f"[CUGA] Checking history_messages: count={len(history_messages) if history_messages else 0}")
            if not history_messages or len(history_messages) == 0:
                logger.debug("[CUGA] First message in history detected, resetting var_manager")
            else:
                logger.debug(f"[CUGA] Continuing conversation with {len(history_messages)} previous messages")

            llm_manager = LLMManager()
            llm_manager.set_llm(llm)
            instructions_manager = InstructionsManager()

            instructions_to_use = self.instructions or ""
            logger.debug(f"[CUGA] instructions are: {instructions_to_use}")
            instructions_manager.set_instructions_from_one_file(instructions_to_use)
            tracker = ActivityTracker()
            tracker.set_tools(tools)
            thread_id = self.graph.session_id
            logger.debug(f"[CUGA] Using thread_id (session_id): {thread_id}")
            cuga_agent = CugaAgent(browser_enabled=self.browser_enabled, thread_id=thread_id)
            if self.browser_enabled:
                await cuga_agent.initialize_freemode_env(start_url=self.web_apps.strip(), interface_mode="browser_only")
            else:
                await cuga_agent.initialize_appworld_env()

            yield {
                "event": "on_chain_start",
                "run_id": str(uuid.uuid4()),
                "name": "CUGA_thinking...",
                "data": {"input": {"input": current_input, "chat_history": []}},
            }
            logger.debug(f"[CUGA] current web apps are {self.web_apps}")
            logger.debug(f"[CUGA] Processing input: {current_input}")
            try:
                # Convert history to LangChain format for the event
                logger.debug(f"[CUGA] Converting {len(history_messages)} history messages to LangChain format")
                lc_messages = []
                for i, msg in enumerate(history_messages):
                    msg_text = getattr(msg, "text", "N/A")[:50] if hasattr(msg, "text") else "N/A"
                    logger.debug(
                        f"[CUGA] Message {i}: type={type(msg)}, sender={getattr(msg, 'sender', 'N/A')}, "
                        f"text={msg_text}..."
                    )
                    if hasattr(msg, "sender") and msg.sender == "Human":
                        lc_messages.append(HumanMessage(content=msg.text))
                    else:
                        lc_messages.append(AIMessage(content=msg.text))

                logger.debug(f"[CUGA] Converted to {len(lc_messages)} LangChain messages")
                await asyncio.sleep(0.5)

                # 2. Build final response
                response_parts = []

                response_parts.append(f"Processed input: '{current_input}'")
                response_parts.append(f"Available tools: {len(tools)}")
                last_event: StreamEvent | None = None
                tool_run_id: str | None = None
                # 3. Chain end event with AgentFinish
                async for event in cuga_agent.run_task_generic_yield(
                    eval_mode=False, goal=current_input, chat_messages=lc_messages
                ):
                    logger.debug(f"[CUGA] recieved event {event}")
                    if last_event is not None and tool_run_id is not None:
                        logger.debug(f"[CUGA] last event {last_event}")
                        try:
                            # TODO: Extract data
                            data_dict = json.loads(last_event.data)
                        except json.JSONDecodeError:
                            data_dict = last_event.data
                        if last_event.name == "CodeAgent" and "code" in data_dict:
                            data_dict = data_dict["code"]
                        yield {
                            "event": "on_tool_end",
                            "run_id": tool_run_id,
                            "name": last_event.name,
                            "data": {"output": data_dict},
                        }
                    if isinstance(event, StreamEvent):
                        tool_run_id = str(uuid.uuid4())
                        last_event = StreamEvent(name=event.name, data=event.data)
                        tool_event = {
                            "event": "on_tool_start",
                            "run_id": tool_run_id,
                            "name": event.name,
                            "data": {"input": {}},
                        }
                        logger.debug(f"[CUGA] Yielding tool_start event: {event.name}")
                        yield tool_event

                    if isinstance(event, AgentResult):
                        task_result = event
                        end_event = {
                            "event": "on_chain_end",
                            "run_id": str(uuid.uuid4()),
                            "name": "CugaAgent",
                            "data": {"output": AgentFinish(return_values={"output": task_result.answer}, log="")},
                        }
                        answer_preview = task_result.answer[:100] if task_result.answer else "None"
                        logger.info(f"[CUGA] Yielding chain_end event with answer: {answer_preview}...")
                        yield end_event

            except (ValueError, TypeError, RuntimeError, ConnectionError) as e:
                logger.error(f"[CUGA] An error occurred: {e!s}")
                logger.error(f"[CUGA] Traceback: {traceback.format_exc()}")
                error_msg = f"CUGA Agent error: {e!s}"
                logger.error(f"[CUGA] Error occurred: {error_msg}")

                # Emit error event
                yield {
                    "event": "on_chain_error",
                    "run_id": str(uuid.uuid4()),
                    "name": "CugaAgent",
                    "data": {"error": error_msg},
                }