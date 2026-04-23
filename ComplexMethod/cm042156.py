def print_car_docs_diff(path):
  base_car_docs = defaultdict(list)
  new_car_docs = defaultdict(list)

  for car in load_base_car_docs(path):
    base_car_docs[car.car_fingerprint].append(car)
  for car in get_all_car_docs():
    new_car_docs[car.car_fingerprint].append(car)

  # Add new platforms to base cars so we can detect additions and removals in one pass
  base_car_docs.update({car: [] for car in new_car_docs if car not in base_car_docs})

  changes = defaultdict(list)
  for base_car_model, base_cars in base_car_docs.items():
    # Match car info changes, and get additions and removals
    new_cars = new_car_docs[base_car_model]
    car_changes, car_additions, car_removals = match_cars(base_cars, new_cars)

    # Removals
    for car_docs in car_removals:
      changes["removals"].append(format_row([car_docs.get_column(column, STAR_ICON, VIDEO_ICON, FOOTNOTE_TAG) for column in Column]))

    # Additions
    for car_docs in car_additions:
      changes["additions"].append(format_row([car_docs.get_column(column, STAR_ICON, VIDEO_ICON, FOOTNOTE_TAG) for column in Column]))

    for new_car, base_car in car_changes:
      # Column changes
      row_diff = build_column_diff(base_car, new_car)
      if ARROW_SYMBOL in row_diff:
        changes["column"].append(row_diff)

      # Detail sentence changes
      if base_car.detail_sentence != new_car.detail_sentence:
        changes["detail"].append(f"- Sentence for {base_car.name} changed!\n" +
                                 "  ```diff\n" +
                                 f"  - {base_car.detail_sentence}\n" +
                                 f"  + {new_car.detail_sentence}\n" +
                                 "  ```")

  # Print diff
  if any(len(c) for c in changes.values()):
    markdown_builder = ["### ⚠️ This PR makes changes to [CARS.md](../blob/master/docs/CARS.md) ⚠️"]

    for title, category in (("## 🔀 Column Changes", "column"), ("## ❌ Removed", "removals"),
                            ("## ➕ Added", "additions"), ("## 📖 Detail Sentence Changes", "detail")):
      if len(changes[category]):
        markdown_builder.append(title)
        if category not in ("detail",):
          markdown_builder.append(COLUMNS)
          markdown_builder.append(COLUMN_HEADER)
        markdown_builder.extend(changes[category])

    print("\n".join(markdown_builder))