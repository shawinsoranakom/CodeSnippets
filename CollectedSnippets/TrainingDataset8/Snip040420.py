def check_for_release_pr(pull):
    label = pull["head"]["label"]

    if label.find("release/") != -1:
        return pull["head"]["ref"]