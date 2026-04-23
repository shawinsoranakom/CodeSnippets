async def test_multiple_questions(tool: AskQuestionTool, session: ChatSession):
    result = await tool._execute(
        user_id=None,
        session=session,
        questions=[
            {
                "question": "Which channel?",
                "options": ["Email", "Slack"],
                "keyword": "channel",
            },
            {
                "question": "How often?",
                "options": ["Daily", "Weekly"],
                "keyword": "frequency",
            },
            {"question": "Any extra notes?"},
        ],
    )

    assert isinstance(result, ClarificationNeededResponse)
    assert len(result.questions) == 3
    assert result.message == "Which channel?; How often?; Any extra notes?"

    assert result.questions[0].keyword == "channel"
    assert result.questions[0].example == "Email, Slack"
    assert result.questions[1].keyword == "frequency"
    assert result.questions[2].keyword == "question-2"
    assert result.questions[2].example is None