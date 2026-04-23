def main():
    parser = argparse.ArgumentParser(description="Tool to create a commit list")

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--create-new", "--create_new", nargs=2)
    group.add_argument("--update-to", "--update_to")
    # I found this flag useful when experimenting with adding new auto-categorizing filters.
    # After running commitlist.py the first time, if you add any new filters in this file,
    # re-running with "rerun_with_new_filters" will update the existing commitlist.csv file,
    # but only affect the rows that were previously marked as "Uncategorized"
    group.add_argument(
        "--rerun-with-new-filters", "--rerun_with_new_filters", action="store_true"
    )
    group.add_argument("--stat", action="store_true")
    group.add_argument("--export-markdown", "--export_markdown", action="store_true")
    group.add_argument(
        "--export-csv-categories", "--export_csv_categories", action="store_true"
    )
    parser.add_argument("--path", default="results/commitlist.csv")
    args = parser.parse_args()

    if args.create_new:
        create_new(args.path, args.create_new[0], args.create_new[1])
        print(
            "Finished creating new commit list. Results have been saved to results/commitlist.csv"
        )
        return
    if args.update_to:
        update_existing(args.path, args.update_to)
        return
    if args.rerun_with_new_filters:
        rerun_with_new_filters(args.path)
        return
    if args.stat:
        commits = CommitList.from_existing(args.path)
        stats = commits.stat()
        pprint.pprint(stats)
        return

    if args.export_csv_categories:
        commits = CommitList.from_existing(args.path)
        categories = list(commits.stat().keys())
        for category in categories:
            print(f"Exporting {category}...")
            filename = f"results/export/result_{category}.csv"
            CommitList.write_to_disk_static(filename, commits.filter(category=category))
        return

    if args.export_markdown:
        commits = CommitList.from_existing(args.path)
        categories = list(commits.stat().keys())
        for category in categories:
            print(f"Exporting {category}...")
            lines = get_markdown_header(category)
            lines += to_markdown(commits, category)
            filename = f"results/export/result_{category}.md"
            os.makedirs(os.path.dirname(filename), exist_ok=True)
            with open(filename, "w") as f:
                f.writelines(lines)
        return
    raise AssertionError