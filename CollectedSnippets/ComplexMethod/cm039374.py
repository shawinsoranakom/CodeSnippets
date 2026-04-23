def recurse(self, node, tree, ax, max_x, max_y, depth=0):
        import matplotlib.pyplot as plt

        # kwargs for annotations without a bounding box
        common_kwargs = dict(
            zorder=100 - 10 * depth,
            xycoords="axes fraction",
        )
        if self.fontsize is not None:
            common_kwargs["fontsize"] = self.fontsize

        # kwargs for annotations with a bounding box
        kwargs = dict(
            ha="center",
            va="center",
            bbox=self.bbox_args.copy(),
            arrowprops=self.arrow_args.copy(),
            **common_kwargs,
        )
        kwargs["arrowprops"]["edgecolor"] = plt.rcParams["text.color"]

        # offset things by .5 to center them in plot
        xy = ((node.x + 0.5) / max_x, (max_y - node.y - 0.5) / max_y)

        if self.max_depth is None or depth <= self.max_depth:
            if self.filled:
                kwargs["bbox"]["fc"] = self.get_fill_color(tree, node.tree.node_id)
            else:
                kwargs["bbox"]["fc"] = ax.get_facecolor()

            if node.parent is None:
                # root
                ax.annotate(node.tree.label, xy, **kwargs)
            else:
                xy_parent = (
                    (node.parent.x + 0.5) / max_x,
                    (max_y - node.parent.y - 0.5) / max_y,
                )
                ax.annotate(node.tree.label, xy_parent, xy, **kwargs)

                # Draw True/False labels if parent is root node
                if node.parent.parent is None:
                    # Adjust the position for the text to be slightly above the arrow
                    text_pos = (
                        (xy_parent[0] + xy[0]) / 2,
                        (xy_parent[1] + xy[1]) / 2,
                    )
                    # Annotate the arrow with the edge label to indicate the child
                    # where the sample-split condition is satisfied
                    if node.parent.left() == node:
                        label_text, label_ha = ("True  ", "right")
                    else:
                        label_text, label_ha = ("  False", "left")
                    ax.annotate(label_text, text_pos, ha=label_ha, **common_kwargs)
            for child in node.children:
                self.recurse(child, tree, ax, max_x, max_y, depth=depth + 1)

        else:
            xy_parent = (
                (node.parent.x + 0.5) / max_x,
                (max_y - node.parent.y - 0.5) / max_y,
            )
            kwargs["bbox"]["fc"] = "grey"
            ax.annotate("\n  (...)  \n", xy_parent, xy, **kwargs)