def visualize_schedule(
    schedule: list[list[_Action | None]],
    filename: str | None = None,
) -> None:
    """
    Visualize the schedule using matplotlib.
    The schedule is a list of lists where each inner list represents a rank and each element in the inner list represents an action.
    The actions are represented as rectangles with different colors based on their computation type.
    The filename is optional and if provided, the plot will be saved to that file.

    Args:
        schedule: The schedule to visualize.
        filename: The filename to save the plot to. If not provided, the plot will be displayed.
        add_schedule_spacing: If True, add spacing to the schedule based on dependencies between ranks.

    """

    import matplotlib.pyplot as plt
    from matplotlib.patches import Rectangle

    plt.rcParams["font.family"] = (
        "DejaVu Sans"  # or any other font available on your system
    )
    num_ranks = len(schedule)
    max_actions = max(len(rank) for rank in schedule)

    # Increase the figure size to provide more space for the legend
    fig, ax = plt.subplots(figsize=(max_actions + 2, num_ranks + 2))
    max_draw_position = -1
    # Calculate dynamic font size based on figure size
    font_size = min(max_actions, num_ranks) + 4
    used_computation = set()
    for rank_idx, actions in enumerate(schedule):
        draw_position = 0  # Initialize drawing position for each rank
        for action in actions:
            if action is not None:
                comp_type_color = action_type_to_color_mapping.get(
                    action.computation_type, _ComputationTypeVisual("black")
                )
                used_computation.add(action.computation_type)
                color = comp_type_color.color
                width = comp_type_color.width

                # Check if action has sub_actions to determine styling
                if action.sub_actions is not None:
                    linewidth = 2  # Thicker border for compound actions
                    text_weight = "normal"  # Bold text for compound actions
                else:
                    linewidth = 1  # Default linewidth for regular actions
                    text_weight = "normal"  # Default text weight

                # Draw the rectangle to represent the action duration
                rect = Rectangle(
                    (draw_position, num_ranks - rank_idx - 1),
                    width,
                    1,
                    facecolor=color,
                    edgecolor="black",
                    linewidth=linewidth,
                )
                ax.add_patch(rect)

                # Draw the text centered within the rectangle
                ax.text(
                    draw_position + width / 2,
                    num_ranks - rank_idx - 1 + 0.5,
                    str(action),
                    ha="center",
                    va="center",
                    fontsize=font_size,
                    color="white",
                    weight=text_weight,
                )

                draw_position += width
            else:
                draw_position += 1  # Move to the next
            max_draw_position = max(max_draw_position, draw_position)
    ax.set_xlim(-0.5, max_draw_position + 1)
    ax.set_ylim(-0.5, num_ranks + 0.5)  # Add extra space at the top
    # Set y-ticks to be in the middle of each rank's row
    ax.set_yticks([num_ranks - rank_idx - 0.5 for rank_idx in range(num_ranks)])
    ax.set_yticklabels([f"Rank {i}" for i in range(num_ranks)], fontsize=font_size)
    ax.set_xticklabels([])

    # Remove grid lines and ticks
    ax.grid(False)
    # Add legend with larger font size
    legend_elements = [
        Rectangle(
            (0, 0),
            1,
            1,
            facecolor=action_type_to_color_mapping[comp_type].color,
            edgecolor="black",
            label=action_type_to_color_mapping[comp_type].text,
        )
        for comp_type in used_computation
    ]
    ax.legend(handles=legend_elements, loc="upper right", fontsize=font_size)
    # Save to file if filename is provided, otherwise display the plot
    if filename:
        plt.savefig(filename, bbox_inches="tight")
    else:
        plt.show()