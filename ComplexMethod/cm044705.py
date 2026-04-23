def update(self):
        """Smart update — detects install method and runs the right update command."""
        if not self.is_installed:
            console.print("[warning]Tool is not installed yet. Install it first.[/warning]")
            return

        updated = False
        for ic in (self.INSTALL_COMMANDS or []):
            if "git clone" in ic:
                # Extract repo dir name from clone command
                parts = ic.split()
                repo_urls = [p for p in parts if p.startswith("http")]
                if repo_urls:
                    dirname = repo_urls[0].rstrip("/").rsplit("/", 1)[-1].replace(".git", "")
                    if os.path.isdir(dirname):
                        console.print(f"[cyan]→ git -C {dirname} pull[/cyan]")
                        os.system(f"git -C {dirname} pull")
                        updated = True
            elif "pip install" in ic:
                # Re-run pip install (--upgrade)
                upgrade_cmd = ic.replace("pip install", "pip install --upgrade")
                console.print(f"[cyan]→ {upgrade_cmd}[/cyan]")
                os.system(upgrade_cmd)
                updated = True
            elif "go install" in ic:
                # Re-run go install (fetches latest)
                console.print(f"[cyan]→ {ic}[/cyan]")
                os.system(ic)
                updated = True
            elif "gem install" in ic:
                upgrade_cmd = ic.replace("gem install", "gem update")
                console.print(f"[cyan]→ {upgrade_cmd}[/cyan]")
                os.system(upgrade_cmd)
                updated = True

        if updated:
            console.print("[success]✔ Update complete![/success]")
        else:
            console.print("[dim]No automatic update method available for this tool.[/dim]")