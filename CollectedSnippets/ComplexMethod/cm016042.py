def handle_commit(self, commit, i, total, commits):
        potential_reverts = self.potential_reverts_of(commit, commits)
        if potential_reverts:
            potential_reverts = f"!!!POTENTIAL REVERTS!!!: {potential_reverts}"
        else:
            potential_reverts = ""

        features = self.features(commit)
        if self.classifier is not None:
            from classifier import CommitClassifierInputs

            # Some commits don't have authors:
            author = features.author if features.author else "Unknown"
            files = " ".join(features.files_changed)
            classifier_input = CommitClassifierInputs(
                title=[features.title], files=[files], author=[author]
            )
            classifier_category = self.classifier.get_most_likely_category_name(
                classifier_input
            )[0]

        else:
            classifier_category = commit.category

        breaking_alarm = ""
        if "module: bc-breaking" in features.labels:
            breaking_alarm += "\n!!!!!! BC BREAKING !!!!!!"

        if "module: deprecation" in features.labels:
            breaking_alarm += "\n!!!!!! DEPRECATION !!!!!!"

        os.system("clear")
        view = textwrap.dedent(
            f"""\
[{i}/{total}]
================================================================================
{features.title}

{potential_reverts} {breaking_alarm}

{features.body}

Files changed: {features.files_changed}

Labels: {features.labels}

Current category: {commit.category}

Select from: {", ".join(common.categories)}

        """
        )
        print(view)
        cat_choice = None
        while cat_choice is None:
            print("Enter category: ")
            value = input(f"{classifier_category} ").strip()
            if len(value) == 0:
                # The user just pressed enter and likes the default value
                cat_choice = classifier_category
                continue
            choices = [cat for cat in common.categories if cat.startswith(value)]
            if len(choices) != 1:
                print(f"Possible matches: {choices}, try again")
                continue
            cat_choice = choices[0]
        print(f"\nSelected: {cat_choice}")
        print(f"\nCurrent topic: {commit.topic}")
        print(f"""Select from: {", ".join(topics)}""")
        topic_choice = None
        while topic_choice is None:
            value = input("topic> ").strip()
            if len(value) == 0:
                topic_choice = commit.topic
                continue
            choices = [cat for cat in topics if cat.startswith(value)]
            if len(choices) != 1:
                print(f"Possible matches: {choices}, try again")
                continue
            topic_choice = choices[0]
        print(f"\nSelected: {topic_choice}")
        self.update_commit(commit, cat_choice, topic_choice)
        return None