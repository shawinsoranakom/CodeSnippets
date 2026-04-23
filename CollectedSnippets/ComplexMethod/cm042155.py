def match_cars(base_cars, new_cars):
  changes = []
  additions = []
  for new in new_cars:
    # Addition if no close matches or close match already used
    # Change if close match and not already used
    matches = difflib.get_close_matches(new.name, [b.name for b in base_cars], cutoff=0.)
    if not len(matches) or matches[0] in [c[1].name for c in changes]:
      additions.append(new)
    else:
      changes.append((new, next(car for car in base_cars if car.name == matches[0])))

  # Removal if base car not in changes
  removals = [b for b in base_cars if b.name not in [c[1].name for c in changes]]
  return changes, additions, removals