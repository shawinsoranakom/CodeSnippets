def generate_processor_intro(cls) -> str:
    """
    Generate the intro docstring for a processor class based on its attributes.

    Args:
        cls: Processor class to generate intro for

    Returns:
        str: Generated intro text
    """
    class_name = cls.__name__

    # Get attributes and their corresponding class names
    attributes = cls.get_attributes()
    if not attributes:
        return ""

    # Build list of component names and their classes
    components = []
    component_classes = []

    for attr in attributes:
        # Get the class name for this attribute
        class_attr = f"{attr}_class"
        # Format attribute name for display
        attr_display = attr.replace("_", " ")
        components.append(attr_display)
        component_classes.append(f"[`{{{class_attr}}}`]")
    if not components:
        return ""

    # Generate the intro text
    if len(components) == 1:
        components_text = f"a {components[0]}"
        classes_text = component_classes[0]
        classes_text_short = component_classes[0].replace("[`", "[`~")
    elif len(components) == 2:
        components_text = f"a {components[0]} and a {components[1]}"
        classes_text = f"{component_classes[0]} and {component_classes[1]}"
        classes_text_short = (
            f"{component_classes[0].replace('[`', '[`~')} and {component_classes[1].replace('[`', '[`~')}"
        )
    else:
        components_text = ", ".join(f"a {c}" for c in components[:-1]) + f", and a {components[-1]}"
        classes_text = ", ".join(component_classes[:-1]) + f", and {component_classes[-1]}"
        classes_short = [c.replace("[`", "[`~") for c in component_classes]
        classes_text_short = ", ".join(classes_short[:-1]) + f", and {classes_short[-1]}"

    intro = f"""Constructs a {class_name} which wraps {components_text} into a single processor.

[`{class_name}`] offers all the functionalities of {classes_text}. See the
{classes_text_short} for more information.
"""

    return intro