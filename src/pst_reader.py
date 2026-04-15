"""PST file reading and recursive message iteration."""

import pypff


def iter_messages(folder, skip_folders: set, path: str = ""):
    """Recursively yield (folder_path, message) skipping unwanted folders."""
    name = folder.name or "(root)"
    current_path = f"{path}/{name}".strip("/")

    if any(s in name.lower() for s in skip_folders):
        return

    for i in range(folder.number_of_sub_messages):
        try:
            yield current_path, folder.get_sub_message(i)
        except Exception:
            continue

    for i in range(folder.number_of_sub_folders):
        try:
            yield from iter_messages(folder.get_sub_folder(i), skip_folders, current_path)
        except Exception:
            continue


def count_messages(folder, skip_folders: set) -> int:
    """Count total messages that will be processed (skipping excluded folders)."""
    name = folder.name or ""
    if any(s in name.lower() for s in skip_folders):
        return 0

    total = folder.number_of_sub_messages
    for i in range(folder.number_of_sub_folders):
        try:
            total += count_messages(folder.get_sub_folder(i), skip_folders)
        except Exception:
            continue
    return total


def list_folders(folder, skip_folders: set, path: str = "", depth: int = 0) -> list[dict]:
    """Return a list of folders with message counts for inspection."""
    name = folder.name or "(root)"
    current_path = f"{path}/{name}".strip("/")
    results = []

    skipped = any(s in name.lower() for s in skip_folders)
    results.append({
        "path": current_path,
        "depth": depth,
        "messages": folder.number_of_sub_messages,
        "skipped": skipped,
    })

    if not skipped:
        for i in range(folder.number_of_sub_folders):
            try:
                sub = folder.get_sub_folder(i)
                results.extend(list_folders(sub, skip_folders, current_path, depth + 1))
            except Exception:
                continue

    return results
