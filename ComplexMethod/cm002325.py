def topological_sort(dependencies: dict) -> list[list[str]]:
    """Given the dependencies graph, construct a sorted list of list of modular files.

    Examples:

        The returned list of lists might be:
        [
            ["../modular_mistral.py", "../modular_gemma.py"],  # level 0
            ["../modular_llama4.py", "../modular_gemma2.py"],  # level 1
            ["../modular_glm4.py"],                            # level 2
        ]
        which means mistral and gemma do not depend on any other modular models, while llama4 and gemma2
        depend on the models in the first list, and glm4 depends on the models in the second and (optionally) in the first list.
    """

    # Nodes are the name of the models to convert (we only add those to the graph)
    nodes = {node.rsplit("modular_", 1)[1].replace(".py", "") for node in dependencies}
    # This will be a graph from models to convert, to models to convert that should be converted before (as they are a dependency)
    graph = {}
    name_mapping = {}
    for node, deps in dependencies.items():
        node_name = node.rsplit("modular_", 1)[1].replace(".py", "")
        dep_names = {dep.split(".")[-2] for dep in deps}
        dependencies = {dep for dep in dep_names if dep in nodes and dep != node_name}
        graph[node_name] = dependencies
        name_mapping[node_name] = node

    sorting_list = []
    while len(graph) > 0:
        # Find the nodes with 0 out-degree
        leaf_nodes = {node for node in graph if len(graph[node]) == 0}
        # Add them to the list as next level
        sorting_list.append([name_mapping[node] for node in leaf_nodes])
        # Remove the leaves from the graph (and from the deps of other nodes)
        graph = {node: deps - leaf_nodes for node, deps in graph.items() if node not in leaf_nodes}

    return sorting_list