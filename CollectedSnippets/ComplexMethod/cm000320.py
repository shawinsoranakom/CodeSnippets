def send_discord_notification(webhook_url: str, pr: "PullRequest", overlaps: list["Overlap"]):
    """Send a Discord notification about significant overlaps."""
    conflicts = [o for o in overlaps if o.has_merge_conflict]
    if not conflicts:
        return

    # Discord limits: max 25 fields, max 1024 chars per field value
    fields = []
    for o in conflicts[:25]:
        other = o.pr_b if o.pr_a.number == pr.number else o.pr_a
        # Build value string with truncation to stay under 1024 chars
        file_list = o.conflict_files[:3]
        files_str = f"Files: `{'`, `'.join(file_list)}`"
        if len(o.conflict_files) > 3:
            files_str += f" (+{len(o.conflict_files) - 3} more)"
        value = f"[{other.title[:100]}]({other.url})\n{files_str}"
        # Truncate if still too long
        if len(value) > 1024:
            value = value[:1020] + "..."
        fields.append({
            "name": f"Conflicts with #{other.number}",
            "value": value,
            "inline": False
        })

    embed = {
        "title": f"⚠️ PR #{pr.number} has merge conflicts",
        "description": f"[{pr.title}]({pr.url})",
        "color": 0xFF0000,
        "fields": fields
    }

    if len(conflicts) > 25:
        embed["footer"] = {"text": f"... and {len(conflicts) - 25} more conflicts"}

    try:
        subprocess.run(
            ["curl", "-X", "POST", "-H", "Content-Type: application/json",
             "--max-time", "10",
             "-d", json.dumps({"embeds": [embed]}), webhook_url],
            capture_output=True,
            timeout=15
        )
    except subprocess.TimeoutExpired:
        print("Warning: Discord webhook timed out", file=sys.stderr)