def template_replace(templates: list[str], replacements: dict[str, list[str]]) -> list[tuple[str]]:
    """Renders templates with possible combinations of replacements.

    Example 1: Suppose that:
      templates = ["dog_breed are awesome", "dog_breed are cool"]
      replacements = {"dog_breed": ["Huskies", "Beagles"]}
    Then we would return:
      [
          ("Huskies are awesome", "Huskies are cool"),
          ("Beagles are awesome", "Beagles are cool")
      ]

    Example 2: Suppose that:
      templates = ["Huskies are word1 but also word2"]
      replacements = {"word1": ["playful", "cute"],
                      "word2": ["feisty", "tiring"]}
    Then we would return:
      [
          ("Huskies are playful but also feisty"),
          ("Huskies are playful but also tiring"),
          ("Huskies are cute but also feisty"),
          ("Huskies are cute but also tiring")
      ]

    Note that if any of the replacements do not occur in any template:
      templates = ["Huskies are word1", "Beagles!"]
      replacements = {"word1": ["playful", "cute"],
                      "word2": ["feisty", "tiring"]}
    Then we do not generate duplicates, returning:
      [
          ("Huskies are playful", "Beagles!"),
          ("Huskies are cute", "Beagles!")
      ]
    """
    # First, build a structure like:
    #   [
    #     [("word1", "playful"), ("word1", "cute")],
    #     [("word2", "feisty"), ("word2", "tiring")]
    #   ]
    replacement_combos = []
    for original, possible_replacements in replacements.items():
        original_replacement_tuples = []
        for replacement in possible_replacements:
            original_replacement_tuples.append((original, replacement))
        replacement_combos.append(original_replacement_tuples)

    # Second, generate rendered templates, including possible duplicates.
    rendered_templates = []
    for replacement_combo in itertools.product(*replacement_combos):
        # replacement_combo would be e.g.
        #   [("word1", "playful"), ("word2", "feisty")]
        templates_with_replacements = []
        for template in templates:
            for original, replacement in replacement_combo:
                template = template.replace(original, replacement)
            templates_with_replacements.append(template)
        rendered_templates.append(tuple(templates_with_replacements))

    # Finally, remove the duplicates (but keep the order).
    rendered_templates_no_duplicates = []
    for x in rendered_templates:
        # Inefficient, but should be fine for our purposes.
        if x not in rendered_templates_no_duplicates:
            rendered_templates_no_duplicates.append(x)

    return rendered_templates_no_duplicates