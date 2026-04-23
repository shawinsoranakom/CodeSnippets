def main() -> None:
    settings = Settings()
    if settings.debug:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)
    logging.debug(f"Using config: {settings.model_dump_json()}")
    g = Github(settings.github_token.get_secret_value())
    repo = g.get_repo(settings.github_repository)
    if not settings.github_event_path.is_file():
        raise RuntimeError(
            f"No github event file available at: {settings.github_event_path}"
        )
    contents = settings.github_event_path.read_text("utf-8")
    github_event = PartialGitHubEvent.model_validate_json(contents)
    logging.info(f"Using GitHub event: {github_event}")
    number = (
        github_event.pull_request and github_event.pull_request.number
    ) or settings.number
    if number is None:
        raise RuntimeError("No PR number available")

    # Avoid race conditions with multiple labels
    sleep_time = random.random() * 10  # random number between 0 and 10 seconds
    logging.info(
        f"Sleeping for {sleep_time} seconds to avoid "
        "race conditions and multiple comments"
    )
    time.sleep(sleep_time)

    # Get PR
    logging.debug(f"Processing PR: #{number}")
    pr = repo.get_pull(number)
    label_strs = {label.name for label in pr.get_labels()}
    langs = []
    for label in label_strs:
        if label.startswith("lang-") and not label == lang_all_label:
            langs.append(label[5:])
    logging.info(f"PR #{pr.number} has labels: {label_strs}")
    if not langs or lang_all_label not in label_strs:
        logging.info(f"PR #{pr.number} doesn't seem to be a translation PR, skipping")
        sys.exit(0)

    # Generate translation map, lang ID to discussion
    discussions = get_graphql_translation_discussions(settings=settings)
    lang_to_discussion_map: dict[str, AllDiscussionsDiscussionNode] = {}
    for discussion in discussions:
        for edge in discussion.labels.edges:
            label = edge.node.name
            if label.startswith("lang-") and not label == lang_all_label:
                lang = label[5:]
                lang_to_discussion_map[lang] = discussion
    logging.debug(f"Using translations map: {lang_to_discussion_map}")

    # Messages to create or check
    new_translation_message = f"Good news everyone! 😉 There's a new translation PR to be reviewed: #{pr.number} by @{pr.user.login}. 🎉 This requires 2 approvals from native speakers to be merged. 🤓"
    done_translation_message = f"~There's a new translation PR to be reviewed: #{pr.number} by @{pr.user.login}~ Good job! This is done. 🍰☕"

    # Normally only one language, but still
    for lang in langs:
        if lang not in lang_to_discussion_map:
            log_message = f"Could not find discussion for language: {lang}"
            logging.error(log_message)
            raise RuntimeError(log_message)
        discussion = lang_to_discussion_map[lang]
        logging.info(
            f"Found a translation discussion for language: {lang} in discussion: #{discussion.number}"
        )

        already_notified_comment: Comment | None = None
        already_done_comment: Comment | None = None

        logging.info(
            f"Checking current comments in discussion: #{discussion.number} to see if already notified about this PR: #{pr.number}"
        )
        comments = get_graphql_translation_discussion_comments(
            settings=settings, discussion_number=discussion.number
        )
        for comment in comments:
            if new_translation_message in comment.body:
                already_notified_comment = comment
            elif done_translation_message in comment.body:
                already_done_comment = comment
        logging.info(
            f"Already notified comment: {already_notified_comment}, already done comment: {already_done_comment}"
        )

        if pr.state == "open" and awaiting_label in label_strs:
            logging.info(
                f"This PR seems to be a language translation and awaiting reviews: #{pr.number}"
            )
            if already_notified_comment:
                logging.info(
                    f"This PR #{pr.number} was already notified in comment: {already_notified_comment.url}"
                )
            else:
                logging.info(
                    f"Writing notification comment about PR #{pr.number} in Discussion: #{discussion.number}"
                )
                comment = create_comment(
                    settings=settings,
                    discussion_id=discussion.id,
                    body=new_translation_message,
                )
                logging.info(f"Notified in comment: {comment.url}")
        elif pr.state == "closed" or approved_label in label_strs:
            logging.info(f"Already approved or closed PR #{pr.number}")
            if already_done_comment:
                logging.info(
                    f"This PR #{pr.number} was already marked as done in comment: {already_done_comment.url}"
                )
            elif already_notified_comment:
                updated_comment = update_comment(
                    settings=settings,
                    comment_id=already_notified_comment.id,
                    body=done_translation_message,
                )
                logging.info(f"Marked as done in comment: {updated_comment.url}")
        else:
            logging.info(
                f"There doesn't seem to be anything to be done about PR #{pr.number}"
            )
    logging.info("Finished")