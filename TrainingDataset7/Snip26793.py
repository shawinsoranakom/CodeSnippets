def repr_changes(self, changes, include_dependencies=False):
        output = ""
        for app_label, migrations_ in sorted(changes.items()):
            output += "  %s:\n" % app_label
            for migration in migrations_:
                output += "    %s\n" % migration.name
                for operation in migration.operations:
                    output += "      %s\n" % operation
                if include_dependencies:
                    output += "      Dependencies:\n"
                    if migration.dependencies:
                        for dep in migration.dependencies:
                            output += "        %s\n" % (dep,)
                    else:
                        output += "        None\n"
        return output