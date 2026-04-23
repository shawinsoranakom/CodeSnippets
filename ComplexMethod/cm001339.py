def get_strategy_class(
    strategy_type: PromptStrategyType,
) -> type[BaseMultiStepPromptStrategy]:
    """Get the strategy class for a given strategy type.

    This is a registry function that returns the appropriate strategy class.
    Import is done lazily to avoid circular imports.
    """
    from .one_shot import OneShotAgentPromptStrategy

    strategy_map: dict[PromptStrategyType, type] = {
        PromptStrategyType.ONE_SHOT: OneShotAgentPromptStrategy,
    }

    # Lazy import for new strategies to avoid circular imports
    if strategy_type == PromptStrategyType.REWOO:
        from .rewoo import ReWOOPromptStrategy

        return ReWOOPromptStrategy
    elif strategy_type == PromptStrategyType.PLAN_EXECUTE:
        from .plan_execute import PlanExecutePromptStrategy

        return PlanExecutePromptStrategy
    elif strategy_type == PromptStrategyType.REFLEXION:
        from .reflexion import ReflexionPromptStrategy

        return ReflexionPromptStrategy
    elif strategy_type == PromptStrategyType.TREE_OF_THOUGHTS:
        from .tree_of_thoughts import TreeOfThoughtsPromptStrategy

        return TreeOfThoughtsPromptStrategy
    elif strategy_type == PromptStrategyType.LATS:
        from .lats import LATSPromptStrategy

        return LATSPromptStrategy
    elif strategy_type == PromptStrategyType.MULTI_AGENT_DEBATE:
        from .multi_agent_debate import MultiAgentDebateStrategy

        return MultiAgentDebateStrategy

    if strategy_type not in strategy_map:
        raise ValueError(f"Unknown strategy type: {strategy_type}")

    return strategy_map[strategy_type]