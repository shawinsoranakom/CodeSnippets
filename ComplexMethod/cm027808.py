def tree_traversal(node: Control):
            if is_element_interactive(node):
                box = node.BoundingRectangle
                x,y=box.xcenter(),box.ycenter()
                center = Center(x=x,y=y)
                interactive_nodes.append(TreeElementNode(
                    name=node.Name.strip() or "''",
                    control_type=node.LocalizedControlType.title(),
                    shortcut=node.AcceleratorKey or "''",
                    bounding_box=BoundingBox(left=box.left,top=box.top,right=box.right,bottom=box.bottom),
                    center=center,
                    app_name=app_name
                ))
            elif is_element_text(node):
                informative_nodes.append(TextElementNode(
                    name=node.Name.strip() or "''",
                    app_name=app_name
                ))
            elif is_element_scrollable(node):
                scroll_pattern=node.GetScrollPattern()
                box = node.BoundingRectangle
                x,y=box.xcenter(),box.ycenter()
                center = Center(x=x,y=y)
                scrollable_nodes.append(ScrollElementNode(
                    name=node.Name.strip() or node.LocalizedControlType.capitalize() or "''",
                    app_name=app_name,
                    control_type=node.LocalizedControlType.title(),
                    center=center,
                    horizontal_scrollable=scroll_pattern.HorizontallyScrollable,
                    vertical_scrollable=scroll_pattern.VerticallyScrollable
                ))

            # Recursively check all children
            for child in node.GetChildren():
                tree_traversal(child)