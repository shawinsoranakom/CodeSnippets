def analyze_resume(
    resume_text: str,
    role: Literal["ai_ml_engineer", "frontend_engineer", "backend_engineer"],
    analyzer: Agent
) -> Tuple[bool, str]:
    try:
        response: RunOutput = analyzer.run(
            f"""Please analyze this resume against the following requirements and provide your response in valid JSON format:
            Role Requirements:
            {ROLE_REQUIREMENTS[role]}
            Resume Text:
            {resume_text}
            Your response must be a valid JSON object like this:
            {{
                "selected": true/false,
                "feedback": "Detailed feedback explaining the decision",
                "matching_skills": ["skill1", "skill2"],
                "missing_skills": ["skill3", "skill4"],
                "experience_level": "junior/mid/senior"
            }}
            Evaluation criteria:
            1. Match at least 70% of required skills
            2. Consider both theoretical knowledge and practical experience
            3. Value project experience and real-world applications
            4. Consider transferable skills from similar technologies
            5. Look for evidence of continuous learning and adaptability
            Important: Return ONLY the JSON object without any markdown formatting or backticks.
            """
        )

        assistant_message = next((msg.content for msg in response.messages if msg.role == 'assistant'), None)
        if not assistant_message:
            raise ValueError("No assistant message found in response.")

        result = json.loads(assistant_message.strip())
        if not isinstance(result, dict) or not all(k in result for k in ["selected", "feedback"]):
            raise ValueError("Invalid response format")

        return result["selected"], result["feedback"]

    except (json.JSONDecodeError, ValueError) as e:
        st.error(f"Error processing response: {str(e)}")
        return False, f"Error analyzing resume: {str(e)}"