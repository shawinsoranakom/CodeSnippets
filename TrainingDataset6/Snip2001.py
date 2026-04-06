def remove_all_removable() -> None:
    all_removable = list_all_removable()
    for removable_path in all_removable:
        removable_path.unlink()
        print(f"Removed: {removable_path}")
    print("Done removing all removable paths")