def get_contributors():
    """Get the list of contributor profiles. Require admin rights."""
    # get core devs and contributor experience team
    core_devs = []
    documentation_team = []
    contributor_experience_team = []
    comm_team = []
    core_devs_slug = "core-devs"
    contributor_experience_team_slug = "contributor-experience-team"
    comm_team_slug = "communication-team"
    documentation_team_slug = "documentation-team"

    entry_point = "https://api.github.com/orgs/scikit-learn/"

    for team_slug, lst in zip(
        (
            core_devs_slug,
            contributor_experience_team_slug,
            comm_team_slug,
            documentation_team_slug,
        ),
        (core_devs, contributor_experience_team, comm_team, documentation_team),
    ):
        print(f"Retrieving {team_slug}\n")
        for page in [1, 2]:  # 30 per page
            reply = get(f"{entry_point}teams/{team_slug}/members?page={page}")
            lst.extend(reply.json())

    # get members of scikit-learn on GitHub
    print("Retrieving members\n")
    members = []
    for page in [1, 2, 3]:  # 30 per page
        reply = get(f"{entry_point}members?page={page}")
        members.extend(reply.json())

    # keep only the logins
    core_devs = set(c["login"] for c in core_devs)
    documentation_team = set(c["login"] for c in documentation_team)
    contributor_experience_team = set(c["login"] for c in contributor_experience_team)
    comm_team = set(c["login"] for c in comm_team)
    members = set(c["login"] for c in members)

    # add missing contributors with GitHub accounts
    members |= {"dubourg", "mbrucher", "thouis", "jarrodmillman"}
    # add missing contributors without GitHub accounts
    members |= {"Angel Soler Gollonet"}
    # remove CI bots
    members -= {"sklearn-ci", "sklearn-wheels", "sklearn-lgtm"}
    contributor_experience_team -= (
        core_devs  # remove ogrisel from contributor_experience_team
    )

    emeritus = (
        members
        - core_devs
        - contributor_experience_team
        - comm_team
        - documentation_team
    )

    # hard coded
    emeritus_contributor_experience_team = {
        "cmarmo",
    }
    emeritus_comm_team = {"reshamas", "laurburke"}

    # Up-to-now, we can subtract the team emeritus from the original emeritus
    emeritus -= emeritus_contributor_experience_team | emeritus_comm_team

    # get profiles from GitHub
    core_devs = [get_profile(login) for login in core_devs]
    emeritus = [get_profile(login) for login in emeritus]
    contributor_experience_team = [
        get_profile(login) for login in contributor_experience_team
    ]
    emeritus_contributor_experience_team = [
        get_profile(login) for login in emeritus_contributor_experience_team
    ]
    comm_team = [get_profile(login) for login in comm_team]
    emeritus_comm_team = [get_profile(login) for login in emeritus_comm_team]
    documentation_team = [get_profile(login) for login in documentation_team]

    # sort by last name
    core_devs = sorted(core_devs, key=key)
    emeritus = sorted(emeritus, key=key)
    contributor_experience_team = sorted(contributor_experience_team, key=key)
    emeritus_contributor_experience_team = sorted(
        emeritus_contributor_experience_team, key=key
    )
    documentation_team = sorted(documentation_team, key=key)
    comm_team = sorted(comm_team, key=key)
    emeritus_comm_team = sorted(emeritus_comm_team, key=key)

    return (
        core_devs,
        emeritus,
        contributor_experience_team,
        emeritus_contributor_experience_team,
        comm_team,
        emeritus_comm_team,
        documentation_team,
    )