def generate_service_types(output, service: ServiceModel, doc=True):
    output.write("from datetime import datetime\n")
    output.write("from enum import StrEnum\n")
    output.write("from typing import IO, TypedDict\n")
    output.write("from collections.abc import Iterable, Iterator\n")
    output.write("\n")
    output.write(
        "from localstack.aws.api import handler, RequestContext, ServiceException, ServiceRequest"
    )
    output.write("\n")

    # ==================================== print type declarations
    nodes: dict[str, ShapeNode] = {}

    for shape_name in service.shape_names:
        shape = service.shape_for(shape_name)
        nodes[to_valid_python_name(shape_name)] = ShapeNode(service, shape)

    # output.write("__all__ = [\n")
    # for name in nodes.keys():
    #     output.write(f'    "{name}",\n')
    # output.write("]\n")

    printed: set[str] = set()
    visited: set[str] = set()
    stack: list[str] = list(nodes.keys())

    stack = sorted(stack, key=lambda name: nodes[name].get_order())
    stack.reverse()

    while stack:
        name = stack.pop()
        if name in printed:
            continue
        node = nodes[name]

        dependencies = [dep for dep in node.dependencies if dep not in printed]

        if not dependencies:
            node.print_declaration(output, doc=doc)
            printed.add(name)
        elif name in visited:
            # break out of circular dependencies
            node.print_declaration(output, doc=doc, quote_types=True)
            printed.add(name)
        else:
            stack.append(name)
            stack.extend(dependencies)
            visited.add(name)