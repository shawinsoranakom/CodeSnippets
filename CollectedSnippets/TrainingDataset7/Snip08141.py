def handle(self, **options):
        self.set_options(**options)
        message = ["\n"]
        if self.dry_run:
            message.append(
                "You have activated the --dry-run option so no files will be "
                "modified.\n\n"
            )

        message.append(
            "You have requested to collect static files at the destination\n"
            "location as specified in your settings"
        )

        if self.is_local_storage() and self.storage.location:
            destination_path = self.storage.location
            message.append(":\n\n    %s\n\n" % destination_path)
            should_warn_user = self.storage.exists(destination_path) and any(
                self.storage.listdir(destination_path)
            )
        else:
            destination_path = None
            message.append(".\n\n")
            # Destination files existence not checked; play it safe and warn.
            should_warn_user = True

        if self.interactive and should_warn_user:
            if self.clear:
                message.append("This will DELETE ALL FILES in this location!\n")
            else:
                message.append("This will overwrite existing files!\n")

            message.append(
                "Are you sure you want to do this?\n\n"
                "Type 'yes' to continue, or 'no' to cancel: "
            )
            if input("".join(message)) != "yes":
                raise CommandError("Collecting static files cancelled.")

        collected = self.collect()

        if self.verbosity >= 1:
            deleted_count = len(collected["deleted"])
            modified_count = len(collected["modified"])
            unmodified_count = len(collected["unmodified"])
            post_processed_count = len(collected["post_processed"])
            skipped_count = len(collected["skipped"])
            return (
                "\n%(deleted)s%(modified_count)s %(identifier)s %(action)s"
                "%(destination)s%(unmodified)s%(post_processed)s%(skipped)s."
            ) % {
                "deleted": (
                    "%s static file%s deleted, "
                    % (deleted_count, "" if deleted_count == 1 else "s")
                    if deleted_count > 0
                    else ""
                ),
                "modified_count": modified_count,
                "identifier": "static file" + ("" if modified_count == 1 else "s"),
                "action": "symlinked" if self.symlink else "copied",
                "destination": (
                    " to '%s'" % destination_path if destination_path else ""
                ),
                "unmodified": (
                    ", %s unmodified" % unmodified_count
                    if collected["unmodified"]
                    else ""
                ),
                "post_processed": (
                    collected["post_processed"]
                    and ", %s post-processed" % post_processed_count
                    or ""
                ),
                "skipped": (
                    ", %s skipped due to conflict" % skipped_count
                    if collected["skipped"]
                    else ""
                ),
            }