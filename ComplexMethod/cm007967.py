def main():
    args = parse_args()

    if args.upgrade_only in ('ejs', 'yt-dlp-ejs'):
        all_updates = update_ejs(verify=args.verify)
    else:
        all_updates = update_requirements(upgrade_only=args.upgrade_only, verify=args.verify)

    if all_updates is None:
        return 1
    elif not all_updates:
        print('All requirements are up-to-date', file=sys.stderr)
        return 0

    if args.verify:
        print('Verification failed! Updates were made:', file=sys.stderr)
        for row in table_a_raza(('package', 'old', 'new'), [
            (package, old or '', new or '')
            for package, (old, new) in all_updates.items()
        ]):
            print(row)
        return 1

    else:
        if not args.no_markdown_reports:
            print(make_pull_request_description(all_updates))
        print(make_commit_message(all_updates))
        return 0