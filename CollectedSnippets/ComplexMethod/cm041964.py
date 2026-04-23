def _choose_retrieved(role_name: str, retrieved: dict) -> Union[None, dict]:
    """
    Retrieved elements have multiple core "curr_events". We need to choose one
    event to which we are going to react to. We pick that event here.
    Args:
      role_name: Current role instance's name whose action we are determining.
      retrieved: A dictionary of <ConceptNode> that were retrieved from the
                 the role's associative memory. This dictionary takes the
                 following form:
                 dictionary[event.description] =
                   {["curr_event"] = <ConceptNode>,
                    ["events"] = [<ConceptNode>, ...],
                    ["thoughts"] = [<ConceptNode>, ...] }
    """
    # Once we are done with the reflection, we might want to build a more
    # complex structure here.

    # We do not want to take self events... for now
    copy_retrieved = retrieved.copy()
    for event_desc, rel_ctx in copy_retrieved.items():
        curr_event = rel_ctx["curr_event"]
        if curr_event.subject == role_name:
            del retrieved[event_desc]

    # Always choose role first.
    priority = []
    for event_desc, rel_ctx in retrieved.items():
        curr_event = rel_ctx["curr_event"]
        if ":" not in curr_event.subject and curr_event.subject != role_name:
            priority += [rel_ctx]
    if priority:
        return random.choice(priority)

    # Skip idle.
    for event_desc, rel_ctx in retrieved.items():
        if "is idle" not in event_desc:
            priority += [rel_ctx]
    if priority:
        return random.choice(priority)
    return None