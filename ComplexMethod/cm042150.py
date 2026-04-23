def get_jenkins_status(branch, commit_sha):
  base_url = f"{JENKINS_URL}/job/openpilot/job/{branch}"
  try:
    # Get list of recent builds
    with urllib.request.urlopen(f"{base_url}/api/json?tree=builds[number,url]", timeout=10) as resp:
      builds = json.loads(resp.read().decode()).get("builds", [])

    # Find build matching commit
    for build in builds[:20]:  # check last 20 builds
      with urllib.request.urlopen(f"{build['url']}api/json", timeout=10) as resp:
        data = json.loads(resp.read().decode())
        for action in data.get("actions", []):
          if action.get("_class") == "hudson.plugins.git.util.BuildData":
            build_sha = action.get("lastBuiltRevision", {}).get("SHA1", "")
            if build_sha.startswith(commit_sha) or commit_sha.startswith(build_sha):
              # Get stages info
              stages = []
              try:
                with urllib.request.urlopen(f"{build['url']}wfapi/describe", timeout=10) as resp2:
                  wf_data = json.loads(resp2.read().decode())
                  stages = [{"name": s["name"], "status": s["status"]} for s in wf_data.get("stages", [])]
              except urllib.error.HTTPError:
                pass
              return {
                "number": data["number"],
                "in_progress": data.get("inProgress", False),
                "result": data.get("result"),
                "url": data.get("url", ""),
                "stages": stages,
              }
    return None  # no build found for this commit
  except urllib.error.HTTPError:
    return None