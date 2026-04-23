def from_state_props(self, state_props: StateProps) -> None:
        super().from_state_props(state_props)
        if self.is_jsonpath_query_language():
            self.items = None
            self.items_path = state_props.get(ItemsPath) or ItemsPath(
                string_sampler=StringJsonPath(JSONPATH_ROOT_PATH)
            )
        else:
            # TODO: add snapshot test to assert what missing definitions of items means for a states map
            self.items_path = None
            self.items = state_props.get(Items)
        self.item_reader = state_props.get(ItemReader)
        self.item_selector = state_props.get(ItemSelector)
        self.parameters = state_props.get(Parargs)
        self.max_concurrency_decl = state_props.get(MaxConcurrencyDecl) or MaxConcurrency()
        self.tolerated_failure_count_decl = (
            state_props.get(ToleratedFailureCountDecl) or ToleratedFailureCountInt()
        )
        self.tolerated_failure_percentage_decl = (
            state_props.get(ToleratedFailurePercentageDecl) or ToleratedFailurePercentage()
        )
        self.result_path = state_props.get(ResultPath) or ResultPath(
            result_path_src=ResultPath.DEFAULT_PATH
        )
        self.result_selector = state_props.get(ResultSelector)
        self.retry = state_props.get(RetryDecl)
        self.catch = state_props.get(CatchDecl)
        self.label = state_props.get(Label)
        self.result_writer = state_props.get(ResultWriter)

        iterator_decl = state_props.get(typ=IteratorDecl)
        item_processor_decl = state_props.get(typ=ItemProcessorDecl)

        if iterator_decl and item_processor_decl:
            raise ValueError("Cannot define both Iterator and ItemProcessor.")

        iteration_decl = iterator_decl or item_processor_decl
        if iteration_decl is None:
            raise ValueError(f"Missing ItemProcessor/Iterator definition in props '{state_props}'.")

        if isinstance(iteration_decl, IteratorDecl):
            self.iteration_component = from_iterator_decl(iteration_decl)
        elif isinstance(iteration_decl, ItemProcessorDecl):
            self.iteration_component = from_item_processor_decl(iteration_decl)
        else:
            raise ValueError(f"Unknown value for IteratorDecl '{iteration_decl}'.")