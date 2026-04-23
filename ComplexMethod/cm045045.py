async def aggregate_final_answer(task: str, client: ChatCompletionClient, team_results, source: str = "Aggregator", cancellation_token: Optional[CancellationToken] = None) -> str:
        """
        team_results: {"team_key": TaskResult}
        team_completion_order: The order in which the teams completed their tasks
        """

        if len(team_results) == 1:
            final_answer = list(team_results.values())[0].messages[-1].content
            aggregator_logger.info(
                f"{source} (Response):\n{final_answer}"
            )
            return final_answer

        assert len(team_results) > 1

        aggregator_messages_to_send = {team_id: deque() for team_id in team_results.keys()} # {team_id: context}

        team_ids = list(team_results.keys())
        current_round = 0
        while (
            not all(len(team_result.messages) == 0 for team_result in team_results.values())
            and ((not resolve_model(client._create_args["model"]) in _MODEL_TOKEN_LIMITS) or client.remaining_tokens([m for messages in aggregator_messages_to_send.values() for m in messages])
            > 2000)
        ):
            team_idx = team_ids[current_round % len(team_ids)]
            if len(team_results[team_idx].messages) > 0:
                m = team_results[team_idx].messages[-1]
                if isinstance(m, ToolCallRequestEvent | ToolCallExecutionEvent):
                    # Ignore tool call messages.
                    pass
                elif isinstance(m, StopMessage | HandoffMessage):
                    aggregator_messages_to_send[team_idx].appendleft(UserMessage(content=m.to_model_text(), source=m.source))
                elif m.source == "MagenticOneOrchestrator":
                    assert isinstance(m, TextMessage | ToolCallSummaryMessage)
                    aggregator_messages_to_send[team_idx].appendleft(AssistantMessage(content=m.to_model_text(), source=m.source))
                else:
                    assert isinstance(m, (TextMessage, MultiModalMessage, ToolCallSummaryMessage))
                    aggregator_messages_to_send[team_idx].appendleft(UserMessage(content=m.to_model_text(), source=m.source))
                team_results[team_idx].messages.pop()
            current_round += 1

        # Log the messages to send
        payload = ""
        for team_idx, messages in aggregator_messages_to_send.items():
            payload += f"\n{'*'*75} \n" f"Team #: {team_idx}" f"\n{'*'*75} \n"
            for message in messages:
                payload += f"\n{'-'*75} \n" f"{message.source}:\n" f"\n{message.content}\n"
            payload += f"\n{'-'*75} \n" f"Team #{team_idx} stop reason:\n" f"\n{team_results[team_idx].stop_reason}\n"
        payload += f"\n{'*'*75} \n"
        aggregator_logger.info(f"{source} (Aggregator Messages):\n{payload}")

        context: List[LLMMessage] = []

        # Add the preamble
        context.append(
            UserMessage(
                content=f"Earlier you were asked the following:\n\n{task}\n\nYour team then worked diligently to address that request. You have been provided with a collection of transcripts and stop reasons from {len(team_results)} different teams to the question. Your task is to carefully evaluate the correctness of each team's response by analyzing their respective transcripts and stop reasons. After considering all perspectives, provide a FINAL ANSWER to the question. It is crucial to critically evaluate the information provided in these responses, recognizing that some of it may be biased or incorrect.",
                source=source,
            )
        )

        for team_idx, aggregator_messages in aggregator_messages_to_send.items():
            context.append(
                UserMessage(
                    content=f"Transcript from Team #{team_idx}:",
                    source=source,
                )
            )
            for message in aggregator_messages:
                context.append(message)
            context.append(
                UserMessage(
                    content=f"Stop reason from Team #{team_idx}:",
                    source=source,
                )
            )
            context.append(
                UserMessage(
                    content=team_results[team_idx].stop_reason if team_results[team_idx].stop_reason else "No stop reason provided.",
                    source=source,
                )
            )

        # ask for the final answer
        context.append(
            UserMessage(
                content=f"""
    Let's think step-by-step. Carefully review the conversation above, critically evaluate the correctness of each team's response, and then output a FINAL ANSWER to the question. The question is repeated here for convenience:

    {task}

    To output the final answer, use the following template: FINAL ANSWER: [YOUR FINAL ANSWER]
    Your FINAL ANSWER should be a number OR as few words as possible OR a comma separated list of numbers and/or strings.
    ADDITIONALLY, your FINAL ANSWER MUST adhere to any formatting instructions specified in the original question (e.g., alphabetization, sequencing, units, rounding, decimal places, etc.)
    If you are asked for a number, express it numerically (i.e., with digits rather than words), don't use commas, and don't include units such as $ or percent signs unless specified otherwise.
    If you are asked for a string, don't use articles or abbreviations (e.g. for cities), unless specified otherwise. Don't output any final sentence punctuation such as '.', '!', or '?'.
    If you are asked for a comma separated list, apply the above rules depending on whether the elements are numbers or strings.
    """.strip(),
                source=source,
            )
        )

        response = await client.create(context, cancellation_token=cancellation_token)
        assert isinstance(response.content, str)

        final_answer = re.sub(r"FINAL ANSWER:", "[FINAL ANSWER]:", response.content)
        aggregator_logger.info(
            f"{source} (Response):\n{final_answer}"
        )

        return re.sub(r"FINAL ANSWER:", "FINAL AGGREGATED ANSWER:", response.content)