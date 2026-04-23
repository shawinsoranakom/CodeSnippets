def write_migration_files(self, changes, update_previous_migration_paths=None):
        """
        Take a changes dict and write them out as migration files.
        """
        directory_created = {}
        for app_label, app_migrations in changes.items():
            if self.verbosity >= 1:
                self.log(self.style.MIGRATE_HEADING("Migrations for '%s':" % app_label))
            for migration in app_migrations:
                # Describe the migration
                writer = MigrationWriter(migration, self.include_header)
                if self.verbosity >= 1:
                    # Display a relative path if it's below the current working
                    # directory, or an absolute path otherwise.
                    migration_string = self.get_relative_path(writer.path)
                    self.log("  %s\n" % self.style.MIGRATE_LABEL(migration_string))
                    for operation in migration.operations:
                        self.log("    %s" % operation.formatted_description())
                    if self.scriptable:
                        self.stdout.write(migration_string)
                if not self.dry_run:
                    # Write the migrations file to the disk.
                    migrations_directory = os.path.dirname(writer.path)
                    if not directory_created.get(app_label):
                        os.makedirs(migrations_directory, exist_ok=True)
                        init_path = os.path.join(migrations_directory, "__init__.py")
                        if not os.path.isfile(init_path):
                            open(init_path, "w").close()
                        # We just do this once per app
                        directory_created[app_label] = True
                    migration_string = writer.as_string()
                    with open(writer.path, "w", encoding="utf-8") as fh:
                        fh.write(migration_string)
                        self.written_files.append(writer.path)
                    if update_previous_migration_paths:
                        prev_path = update_previous_migration_paths[app_label]
                        rel_prev_path = self.get_relative_path(prev_path)
                        if writer.needs_manual_porting:
                            migration_path = self.get_relative_path(writer.path)
                            self.log(
                                self.style.WARNING(
                                    f"Updated migration {migration_path} requires "
                                    f"manual porting.\n"
                                    f"Previous migration {rel_prev_path} was kept and "
                                    f"must be deleted after porting functions manually."
                                )
                            )
                        else:
                            os.remove(prev_path)
                            self.log(f"Deleted {rel_prev_path}")
                elif self.verbosity == 3:
                    # Alternatively, makemigrations --dry-run --verbosity 3
                    # will log the migrations rather than saving the file to
                    # the disk.
                    self.log(
                        self.style.MIGRATE_HEADING(
                            "Full migrations file '%s':" % writer.filename
                        )
                    )
                    self.log(writer.as_string())
        run_formatters(self.written_files, stderr=self.stderr)