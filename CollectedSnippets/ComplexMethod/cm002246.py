def main():
    """CLI entry point for the modular model detector."""
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    parser = argparse.ArgumentParser(prog="hf-code-sim")
    parser.add_argument("--build", action="store_true")
    parser.add_argument("--modeling-file", type=str, help='You can just specify "vits" if you are lazy like me.')
    parser.add_argument(
        "--push-new-index", action="store_true", help="After --build, push index files to a Hub dataset."
    )
    parser.add_argument(
        "--hub-dataset", type=str, default=HUB_DATASET_DEFAULT, help="Hub dataset repo id to pull/push the index."
    )
    parser.add_argument("--use_jaccard", type=bool, default=False, help="Whether or not to use jaccard index")
    args = parser.parse_args()

    analyzer = CodeSimilarityAnalyzer(hub_dataset=args.hub_dataset)

    if args.build:
        analyzer.build_index()
        if args.push_new_index:
            analyzer.push_index_to_hub()
        return

    if not args.modeling_file:
        raise SystemExit("Provide --modeling-file or use --build")

    dates = build_date_data()
    modeling_file = args.modeling_file
    if os.sep not in modeling_file:
        modeling_file = os.path.join("src", "transformers", "models", modeling_file, f"modeling_{modeling_file}.py")

    results = analyzer.analyze_file(
        Path(modeling_file), top_k_per_item=5, allow_hub_fallback=True, use_jaccard=args.use_jaccard
    )
    modeling_filename = Path(modeling_file).name
    release_key = modeling_filename.split("modeling_")[-1][:-3]
    release_date = dates.get(release_key, "unknown release date")

    aggregate_scores: dict[str, float] = {}
    for data in results.values():
        for identifier, score in data.get("embedding", []):
            try:
                relative_path, _ = identifier.split(":", 1)
            except ValueError:
                continue
            aggregate_scores[relative_path] = aggregate_scores.get(relative_path, 0.0) + score

    best_candidate_path: str | None = None
    if aggregate_scores:
        best_candidate_path = max(aggregate_scores.items(), key=lambda item: item[1])[0]
        best_model = Path(best_candidate_path).parts[0] if Path(best_candidate_path).parts else "?"
        best_release = dates.get(best_model, "unknown release date")
        logging.info(
            f"{ANSI_HIGHLIGHT_CANDIDATE}Closest overall candidate: {MODELS_ROOT / best_candidate_path}"
            f" (release: {best_release}, total score: {aggregate_scores[best_candidate_path]:.4f}){ANSI_RESET}"
        )

    grouped: dict[str, list[tuple[str, dict]]] = {"class": [], "function": []}
    for query_name, data in results.items():
        kind = data.get("kind", "function")
        grouped.setdefault(kind, []).append((query_name, data))

    section_titles = [("class", "Classes"), ("function", "Functions")]
    legend_shown = False
    for kind, title in section_titles:
        entries = grouped.get(kind, [])
        if not entries:
            continue

        metrics_present: set[str] = set()
        for _, data in entries:
            if data.get("embedding"):
                metrics_present.add("embedding")
            if args.use_jaccard:
                if data.get("jaccard"):
                    metrics_present.add("jaccard")
                if data.get("intersection"):
                    metrics_present.add("intersection")

        include_metric_column = bool(metrics_present - {"embedding"})
        headers = ["Symbol", "Path", "Score", "Release"]
        if include_metric_column:
            headers = ["Symbol", "Metric", "Path", "Score", "Release"]

        table_rows: list[tuple[str, ...] | None] = []
        row_styles: list[str] = []
        has_metric_rows = False

        logging.info(_colorize_heading(title))

        for query_name, data in entries:
            if table_rows:
                table_rows.append(None)

            symbol_label = query_name
            if release_date:
                symbol_label = f"{symbol_label}"

            symbol_row = (symbol_label,) + ("",) * (len(headers) - 1)
            table_rows.append(symbol_row)
            row_styles.append(ANSI_BOLD)

            embedding_details: list[tuple[str, str, str, float, str]] = []
            embedding_style_indices: list[int] = []

            for identifier, score in data.get("embedding", []):
                try:
                    relative_path, match_name = identifier.split(":", 1)
                except ValueError:
                    continue
                model_id = Path(relative_path).parts[0] if Path(relative_path).parts else "?"
                match_release = dates.get(model_id, "unknown release date")
                full_path, line = _resolve_definition_location(relative_path, match_name)
                display_path = f"{full_path}:{line} ({match_name})"

                if include_metric_column:
                    row = ("", "embedding", display_path, f"{score:.4f}", match_release)
                else:
                    row = ("", display_path, f"{score:.4f}", match_release)

                table_rows.append(row)
                row_styles.append(ANSI_ROW)
                embedding_style_indices.append(len(row_styles) - 1)
                embedding_details.append((relative_path, model_id, match_name, score, match_release))
                has_metric_rows = True

            if embedding_details:
                highest_score = None
                highest_idx = None
                for idx, (_, _, _, score, _) in enumerate(embedding_details):
                    if highest_score is None or score > highest_score:
                        highest_score = score
                        highest_idx = idx

                if highest_idx is not None:
                    row_styles[embedding_style_indices[highest_idx]] = ANSI_HIGHLIGHT_TOP

                if highest_score is not None:
                    oldest_idx = None
                    oldest_date = None
                    for idx, (_, model_id, _, score, release_value) in enumerate(embedding_details):
                        if highest_score - score > 0.1:
                            continue
                        parsed = _parse_release_date(release_value)
                        if parsed is None:
                            continue
                        if oldest_date is None or parsed < oldest_date:
                            oldest_date = parsed
                            oldest_idx = idx
                    if (
                        oldest_idx is not None
                        and row_styles[embedding_style_indices[oldest_idx]] != ANSI_HIGHLIGHT_TOP
                    ):
                        row_styles[embedding_style_indices[oldest_idx]] = ANSI_HIGHLIGHT_OLD

                if best_candidate_path is not None:
                    for idx, (relative_path, _, _, _, _) in enumerate(embedding_details):
                        style_position = embedding_style_indices[idx]
                        if row_styles[style_position] != ANSI_ROW:
                            continue
                        if relative_path == best_candidate_path:
                            row_styles[style_position] = ANSI_HIGHLIGHT_CANDIDATE

            if args.use_jaccard:
                for identifier, score in data.get("jaccard", []):
                    try:
                        relative_path, match_name = identifier.split(":", 1)
                    except ValueError:
                        continue
                    model_id = Path(relative_path).parts[0] if Path(relative_path).parts else "?"
                    match_release = dates.get(model_id, "unknown release date")
                    full_path, line = _resolve_definition_location(relative_path, match_name)
                    display_path = f"{full_path}:{line} ({match_name})"

                    if include_metric_column:
                        row = ("", "jaccard", display_path, f"{score:.4f}", match_release)
                    else:
                        row = ("", display_path, f"{score:.4f}", match_release)

                    table_rows.append(row)
                    row_styles.append(ANSI_ROW)
                    has_metric_rows = True
                    if best_candidate_path == relative_path:
                        row_styles[-1] = ANSI_HIGHLIGHT_CANDIDATE

                for identifier in sorted(data.get("intersection", [])):
                    try:
                        relative_path, match_name = identifier.split(":", 1)
                    except ValueError:
                        continue
                    model_id = Path(relative_path).parts[0] if Path(relative_path).parts else "?"
                    match_release = dates.get(model_id, "unknown release date")
                    full_path, line = _resolve_definition_location(relative_path, match_name)
                    display_path = f"{full_path}:{line} ({match_name})"

                    if include_metric_column:
                        row = ("", "intersection", display_path, "--", match_release)
                    else:
                        row = ("", display_path, "--", match_release)

                    table_rows.append(row)
                    row_styles.append(ANSI_ROW)
                    has_metric_rows = True
                    if best_candidate_path == relative_path:
                        row_styles[-1] = ANSI_HIGHLIGHT_CANDIDATE

        if table_rows:
            if not legend_shown and has_metric_rows:
                logging.info(
                    "Legend: "
                    f"{ANSI_HIGHLIGHT_TOP}highest match{ANSI_RESET}, "
                    f"{ANSI_HIGHLIGHT_OLD}oldest within 0.1{ANSI_RESET}, "
                    f"{ANSI_HIGHLIGHT_CANDIDATE}closest overall candidate{ANSI_RESET}"
                )
                legend_shown = True

            logging.info(_format_table(headers, table_rows, row_styles))
            logging.info("")