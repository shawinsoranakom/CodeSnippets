def _calculate_points(
    agent: prisma.models.StoreAgent,
    categories: list[str],
    custom: list[str],
    integrations: list[str],
) -> int:
    """
    Calculates the total points for an agent based on the specified criteria.

    Args:
        agent: The agent object.
        categories (list[str]): List of categories to match.
        words (list[str]): List of words to match in the description.

    Returns:
        int: Total points for the agent.
    """
    points = 0

    # 1. Category Matches
    matched_categories = sum(
        1 for category in categories if category in agent.categories
    )
    points += matched_categories * 100

    # 2. Description Word Matches
    description_words = agent.description.split()  # Split description into words
    matched_words = sum(1 for word in custom if word in description_words)
    points += matched_words * 100

    matched_words = sum(1 for word in integrations if word in description_words)
    points += matched_words * 50

    # 3. Featured Bonus
    if agent.featured:
        points += 50

    # 4. Rating Bonus
    points += agent.rating * 10

    # 5. Runs Bonus
    runs_points = min(agent.runs / 1000 * 100, 100)  # Cap at 100 points
    points += runs_points

    return int(points)