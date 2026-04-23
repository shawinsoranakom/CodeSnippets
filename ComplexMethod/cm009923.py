def _wrap_in_chain_factory(
    llm_or_chain_factory: MODEL_OR_CHAIN_FACTORY,
    dataset_name: str = "<my_dataset>",
) -> MCF:
    """Wrap in a chain factory.

    Forgive the user if they pass in a chain without memory instead of a chain
    factory. It's a common mistake. Raise a more helpful error message as well.
    """
    if isinstance(llm_or_chain_factory, Chain):
        chain = llm_or_chain_factory
        chain_class = chain.__class__.__name__
        if llm_or_chain_factory.memory is not None:
            memory_class = chain.memory.__class__.__name__
            msg = (
                "Cannot directly evaluate a chain with stateful memory."
                " To evaluate this chain, pass in a chain constructor"
                " that initializes fresh memory each time it is called."
                "  This will safeguard against information"
                " leakage between dataset examples."
                "\nFor example:\n\n"
                "def chain_constructor():\n"
                f"    new_memory = {memory_class}(...)\n"
                f"    return {chain_class}"
                "(memory=new_memory, ...)\n\n"
                f'run_on_dataset("{dataset_name}", chain_constructor, ...)'
            )
            raise ValueError(msg)
        return lambda: chain
    if isinstance(llm_or_chain_factory, BaseLanguageModel):
        return llm_or_chain_factory
    if isinstance(llm_or_chain_factory, Runnable):
        # Memory may exist here, but it's not elegant to check all those cases.
        lcf = llm_or_chain_factory
        return lambda: lcf
    if callable(llm_or_chain_factory):
        if is_traceable_function(llm_or_chain_factory):
            runnable_ = as_runnable(cast("Callable", llm_or_chain_factory))
            return lambda: runnable_
        try:
            _model = llm_or_chain_factory()  # type: ignore[call-arg]
        except TypeError:
            # It's an arbitrary function, wrap it in a RunnableLambda
            user_func = cast("Callable", llm_or_chain_factory)
            sig = inspect.signature(user_func)
            logger.info("Wrapping function %s as RunnableLambda.", sig)
            wrapped = RunnableLambda(user_func)
            return lambda: wrapped
        constructor = cast("Callable", llm_or_chain_factory)
        if isinstance(_model, BaseLanguageModel):
            # It's not uncommon to do an LLM constructor instead of raw LLM,
            # so we'll unpack it for the user.
            return _model
        if is_traceable_function(cast("Callable", _model)):
            runnable_ = as_runnable(cast("Callable", _model))
            return lambda: runnable_
        if not isinstance(_model, Runnable):
            # This is unlikely to happen - a constructor for a model function
            return lambda: RunnableLambda(constructor)
        # Typical correct case
        return constructor
    return llm_or_chain_factory