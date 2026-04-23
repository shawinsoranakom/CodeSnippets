def format_understanding_for_prompt(understanding: BusinessUnderstanding) -> str:
    """Format business understanding as text for system prompt injection."""
    if not understanding:
        return ""
    sections = []

    # User info section
    user_info = []
    if understanding.user_name:
        user_info.append(f"Name: {understanding.user_name}")
    if understanding.job_title:
        user_info.append(f"Job Title: {understanding.job_title}")
    if user_info:
        sections.append("## User\n" + "\n".join(user_info))

    # Business section
    business_info = []
    if understanding.business_name:
        business_info.append(f"Company: {understanding.business_name}")
    if understanding.industry:
        business_info.append(f"Industry: {understanding.industry}")
    if understanding.business_size:
        business_info.append(f"Size: {understanding.business_size}")
    if understanding.user_role:
        business_info.append(f"Role Context: {understanding.user_role}")
    if business_info:
        sections.append("## Business\n" + "\n".join(business_info))

    # Processes section
    processes = []
    if understanding.key_workflows:
        processes.append(f"Key Workflows: {', '.join(understanding.key_workflows)}")
    if understanding.daily_activities:
        processes.append(
            f"Daily Activities: {', '.join(understanding.daily_activities)}"
        )
    if processes:
        sections.append("## Processes\n" + "\n".join(processes))

    # Pain points section
    pain_points = []
    if understanding.pain_points:
        pain_points.append(f"Pain Points: {', '.join(understanding.pain_points)}")
    if understanding.bottlenecks:
        pain_points.append(f"Bottlenecks: {', '.join(understanding.bottlenecks)}")
    if understanding.manual_tasks:
        pain_points.append(f"Manual Tasks: {', '.join(understanding.manual_tasks)}")
    if pain_points:
        sections.append("## Pain Points\n" + "\n".join(pain_points))

    # Goals section
    if understanding.automation_goals:
        sections.append(
            "## Automation Goals\n"
            + "\n".join(f"- {goal}" for goal in understanding.automation_goals)
        )

    # Current tools section
    tools_info = []
    if understanding.current_software:
        tools_info.append(
            f"Current Software: {', '.join(understanding.current_software)}"
        )
    if understanding.existing_automation:
        tools_info.append(
            f"Existing Automation: {', '.join(understanding.existing_automation)}"
        )
    if tools_info:
        sections.append("## Current Tools\n" + "\n".join(tools_info))

    # Additional notes
    if understanding.additional_notes:
        sections.append(f"## Additional Context\n{understanding.additional_notes}")

    if not sections:
        return ""

    return "# User Business Context\n\n" + "\n\n".join(sections)