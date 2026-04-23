def extract_tar_safely(source: Path, base: Path) -> None:
        pending_links: list[tuple[tarfile.TarInfo, Path]] = []
        with tarfile.open(source, "r:gz") as archive:
            for member in archive.getmembers():
                target = safe_extract_path(base, member.name)
                if member.isdir():
                    target.mkdir(parents = True, exist_ok = True)
                    continue
                if member.islnk() or member.issym():
                    pending_links.append((member, target))
                    continue
                if not member.isfile():
                    raise PrebuiltFallback(
                        f"tar archive contained an unsupported entry: {member.name}"
                    )
                target.parent.mkdir(parents = True, exist_ok = True)
                extracted = archive.extractfile(member)
                if extracted is None:
                    raise PrebuiltFallback(
                        f"tar archive entry could not be read: {member.name}"
                    )
                with extracted, target.open("wb") as dst:
                    shutil.copyfileobj(extracted, dst)

        unresolved = list(pending_links)
        while unresolved:
            next_round: list[tuple[tarfile.TarInfo, Path]] = []
            progressed = False
            for member, target in unresolved:
                normalized_link, resolved_target = safe_link_target(
                    base, member.name, member.linkname, target
                )
                if not resolved_target.exists() and not resolved_target.is_symlink():
                    next_round.append((member, target))
                    continue
                if resolved_target.is_dir():
                    raise PrebuiltFallback(
                        f"archive link targeted a directory: {member.name} -> {member.linkname}"
                    )

                target.parent.mkdir(parents = True, exist_ok = True)
                if target.exists() or target.is_symlink():
                    target.unlink()

                if member.issym():
                    target.symlink_to(normalized_link)
                else:
                    shutil.copy2(resolved_target, target)
                progressed = True

            if not progressed:
                details = ", ".join(
                    f"{member.name} -> {member.linkname}" for member, _ in next_round
                )
                raise PrebuiltFallback(
                    f"tar archive contained unresolved link entries: {details}"
                )
            unresolved = next_round