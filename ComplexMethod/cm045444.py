def __init__(
        self,
        name: str,
        group_topic_type: str,
        output_topic_type: str,
        participant_topic_types: List[str],
        participant_names: List[str],
        participant_descriptions: List[str],
        output_message_queue: asyncio.Queue[BaseAgentEvent | BaseChatMessage | GroupChatTermination],
        termination_condition: TerminationCondition | None,
        max_turns: int | None,
        message_factory: MessageFactory,
        graph: DiGraph,
    ) -> None:
        """Initialize the graph-based execution manager."""
        super().__init__(
            name=name,
            group_topic_type=group_topic_type,
            output_topic_type=output_topic_type,
            participant_topic_types=participant_topic_types,
            participant_names=participant_names,
            participant_descriptions=participant_descriptions,
            output_message_queue=output_message_queue,
            termination_condition=termination_condition,
            max_turns=max_turns,
            message_factory=message_factory,
        )
        graph.graph_validate()
        if graph.get_has_cycles() and self._termination_condition is None and self._max_turns is None:
            raise ValueError("A termination condition is required for cyclic graphs without a maximum turn limit.")
        self._graph = graph
        # Lookup table for incoming edges for each node.
        self._parents = graph.get_parents()
        # Lookup table for outgoing edges for each node.
        self._edges: Dict[str, List[DiGraphEdge]] = {n: node.edges for n, node in graph.nodes.items()}

        # Build activation and enqueued_any lookup tables by collecting all edges and grouping by target node
        self._build_lookup_tables(graph)

        # Track which activation groups were triggered for each node
        self._triggered_activation_groups: Dict[str, Set[str]] = {}
        # === Mutable states for the graph execution ===
        # Count the number of remaining parents to activate each node.
        self._remaining: Dict[str, Counter[str]] = {
            target: Counter(groups) for target, groups in graph.get_remaining_map().items()
        }
        # cache for remaining
        self._origin_remaining: Dict[str, Dict[str, int]] = {
            target: Counter(groups) for target, groups in self._remaining.items()
        }

        # Ready queue for nodes that are ready to execute, starting with the start nodes.
        self._ready: Deque[str] = deque([n for n in graph.get_start_nodes()])