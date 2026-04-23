def __init__(
        self,
        root: torch.nn.Module | dict[str, Any],
        graph: Graph,
        class_name: str = "GraphModule",
    ) -> None:
        """
        Construct a GraphModule.

        Args:

            root (Union[torch.nn.Module, Dict[str, Any]):
                ``root`` can either be an nn.Module instance or a Dict mapping strings to any attribute type.
                In the case that ``root`` is a Module, any references to Module-based objects (via qualified
                name) in the Graph's Nodes' ``target`` field will be copied over from the respective place
                within ``root``'s Module hierarchy into the GraphModule's module hierarchy.
                In the case that ``root`` is a dict, the qualified name found in a Node's ``target`` will be
                looked up directly in the dict's keys. The object mapped to by the Dict will be copied
                over into the appropriate place within the GraphModule's module hierarchy.

            graph (Graph): ``graph`` contains the nodes this GraphModule should use for code generation

            class_name (str): ``name`` denotes the name of this GraphModule for debugging purposes. If it's unset, all
                error messages will report as originating from ``GraphModule``. It may be helpful to set this
                to ``root``'s original name or a name that makes sense within the context of your transform.
        """
        super().__init__()
        self.__class__.__name__ = class_name
        if isinstance(root, torch.nn.Module):
            if hasattr(root, "training"):
                self.training = root.training

            # When we pickle/unpickle graph module, we don't want to drop any module or attributes.
            if isinstance(root, _CodeOnlyModule):
                for k, _ in root.named_children():
                    _copy_attr(root, self, k)

                for k, _ in root.named_buffers():
                    _copy_attr(root, self, k)

                for k, _ in root.named_parameters():
                    _copy_attr(root, self, k)

            for node in graph.nodes:
                if node.op in ["get_attr", "call_module"]:
                    if not isinstance(node.target, str):
                        raise AssertionError(
                            f"Expected node.target to be str, got {type(node.target)}"
                        )
                    _copy_attr(root, self, node.target)
        elif isinstance(root, dict):
            targets_to_copy = []
            for node in graph.nodes:
                if node.op in ["get_attr", "call_module"]:
                    if not isinstance(node.target, str):
                        raise AssertionError(
                            f"Expected node.target to be str, got {type(node.target)}"
                        )
                    if node.target not in root:
                        raise RuntimeError(
                            "Node "
                            + str(node)
                            + " referenced target "
                            + node.target
                            + " but that target was not provided in ``root``!"
                        )
                    targets_to_copy.append(node.target)
            # Sort targets in ascending order of the # of atoms.
            # This will ensure that less deeply nested attributes are assigned
            # before more deeply nested attributes. For example, foo.bar
            # will be assigned before foo.bar.baz. Otherwise, we might assign
            # the user-provided ``foo.bar`` and wipe out the previously-assigned
            # ``foo.bar.baz``
            targets_to_copy.sort(key=lambda t: t.count("."))
            for target_to_copy in targets_to_copy:
                _assign_attr(root[target_to_copy], self, target_to_copy)
        else:
            raise RuntimeError("Unsupported type " + str(root) + " passed for root!")

        self.graph = graph

        # Store the Tracer class responsible for creating a Graph separately as part of the
        # GraphModule state, except when the Tracer is defined in a local namespace.
        # Locally defined Tracers are not pickleable. This is needed because torch.package will
        # serialize a GraphModule without retaining the Graph, and needs to use the correct Tracer
        # to re-create the Graph during deserialization.
        self._tracer_cls = None
        if (
            self.graph._tracer_cls
            and "<locals>" not in self.graph._tracer_cls.__qualname__
        ):
            # pyrefly: ignore [bad-assignment]
            self._tracer_cls = self.graph._tracer_cls

        self._tracer_extras = {}
        if self.graph._tracer_extras:
            self._tracer_extras = self.graph._tracer_extras

        # Dictionary to store metadata
        self.meta: dict[str, Any] = {}
        self._replace_hooks: list[Callable[[Node, str, Node], object]] = []
        self._create_node_hooks: list[Callable[[Node], object]] = []
        self._erase_node_hooks: list[Callable[[Node], object]] = []
        # Used to remove hooks from deepcopied graph modules within a context manager.
        self._deepcopy_hooks: list[Callable[[GraphModule], object]] = []
        self.shape_env = None