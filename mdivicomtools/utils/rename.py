import os
import re
import shutil
from pathlib import Path
from typing import List, Optional, Dict, Set
import pandas as pd
import logging
from mdivicomtools.utils.logging import setup_logging
from typing import List, Optional

def sanitize_filename(name):
    # Replace spaces with underscores
    name = name.replace(" ", "_")
    # Remove or replace special characters
    name = re.sub(r'[\/:*?"<>|`%&=]', "", name)
    # replace german umlauts
    name = name.replace("ä", "ae").replace("ö", "oe").replace("ü", "ue").replace("ß", "ss")
    # Ensure the filename is not reserved or ends with a space/period
    reserved_names = {"CON", "PRN", "AUX", "NUL", "COM1", "COM2", "COM3", "COM4", "COM5",
                      "COM6", "COM7", "COM8", "COM9", "LPT1", "LPT2", "LPT3", "LPT4",
                      "LPT5", "LPT6", "LPT7", "LPT8", "LPT9"}
    if name.upper() in reserved_names:
        name += "_safe"
    name = name.rstrip(". ")
    return name


def get_file_list(base_dir: str, omit_hidden: bool = True) -> List[Path]:
    """
    Recursively retrieves a list of files with full paths from a directory,
    omitting hidden files, folders, and Git-related content.

    Args:
        base_dir (str): The main directory to search in.
        omit_hidden (bool): Whether to omit hidden files and directories.

    Returns:
        List[Path]: A list of paths for all eligible files.
    """
    file_list = []
    base_path = Path(base_dir)
    for root, dirs, files in os.walk(base_path):
        # Exclude hidden directories and `.git`
        if omit_hidden:
            dirs[:] = [d for d in dirs if not d.startswith('.') and d != '.git']
        # Exclude hidden files
        for f in files:
            if omit_hidden and f.startswith('.'):
                continue
            file_list.append(Path(root) / f)
    return file_list


def transform_path(
        original_path: Path,
        find_strings: List[str],
        replace_strings: Optional[List[str]],
        prefix: str,
        base_dir: Path,
        securecopy_dir: Path,
        partial_strict: bool = True  # New parameter
) -> (Path, bool):
    """
    Apply find/replace/prefix transformations to a given path and relocate it
    under the securecopy directory, preserving relative structure.

    If replace_strings is None, we only add the prefix to the found strings.
    If replace_strings is not None, we replace each find_string with prefix+corresponding replace_string.

    When partial_strict is True, replacements are applied only for exact word boundaries.

    Args:
        original_path (Path): The original file path to transform.
        find_strings (List[str]): List of strings to find in the path.
        replace_strings (Optional[List[str]]): List of corresponding replacement strings.
        prefix (str): A prefix to prepend to matched strings or replacements.
        base_dir (Path): The base directory of the original file path.
        securecopy_dir (Path): The directory where the transformed path will be relocated.
        partial_strict (bool): If True, only exact word-boundary matches will be replaced.

    Returns:
        Tuple[Path, bool]: The transformed path under the securecopy directory and a
        warning flag for partial matches.
    """
    relative_path = original_path.relative_to(base_dir)
    original_str = str(relative_path)
    new_path_str = original_str

    if replace_strings:
        if len(find_strings) != len(replace_strings):
            raise ValueError("The find_strings and replace_strings must have the same length.")
        # Replace each find_str with prefix+replace_str
        for f_str, r_str in zip(find_strings, replace_strings):
            if partial_strict:
                # Replace only on word boundaries
                new_path_str = re.sub(rf"\b{re.escape(f_str)}\b", f"{prefix}{r_str}", new_path_str)
            else:
                # Allow partial matches
                new_path_str = re.sub(re.escape(f_str), f"{prefix}{r_str}", new_path_str)
    else:
        # No replace_strings means we just prefix the found strings themselves
        for f_str in find_strings:
            if partial_strict:
                # Replace only on word boundaries
                new_path_str = re.sub(rf"\b{re.escape(f_str)}\b", f"{prefix}{f_str}", new_path_str)
            else:
                # Allow partial matches
                new_path_str = re.sub(re.escape(f_str), f"{prefix}{f_str}", new_path_str)

    new_path = securecopy_dir / new_path_str

    # Check if any replacement was done
    replacement_done = (new_path_str != original_str)
    partial_warning = False
    if replacement_done and not partial_strict:
        # For each find_str, check if it was present and if it aligns with word boundaries
        for f_str in find_strings:
            if f_str in original_str:
                # Check word boundary conditions
                word_boundary_pattern = r"\b" + re.escape(f_str) + r"\b"
                if not re.search(word_boundary_pattern, original_str):
                    # The match might be partial (no word boundaries)
                    partial_warning = True

    return new_path, partial_warning


def plan_transformations(
        base_dir: str,
        paths: List[Path],
        find_strings: List[str],
        replace_strings: Optional[List[str]],
        prefix: str = "",
        securecopy_folder: str = "securecopy",
        partial_strict: bool = True
) -> Dict[Path, Path]:
    """
    Given a list of paths, plan the transformations and return a dictionary
    mapping from original_path to new_path, located under a securecopy directory.

    Args:
        base_dir (str): The base directory of the original files.
        paths (List[Path]): The files to transform.
        find_strings (List[str]): Patterns to find.
        replace_strings (Optional[List[str]]): Corresponding replacements.
        prefix (str): Optional prefix to add to the replaced substring.
        securecopy_folder_name (str): Name of the folder where transformed files will be placed.

    Returns:
        Dict[Path, Path]: A mapping of original_path -> transformed_path.
    """
    base_path = Path(base_dir)
    securecopy_dir = base_path / securecopy_folder
    transformation_map = {}

    for p in paths:
        new_p, partial_warning = transform_path(
            original_path=p,
            find_strings=find_strings,
            replace_strings=replace_strings,
            prefix=prefix,
            base_dir=base_path,
            securecopy_dir=securecopy_dir,
            partial_strict=partial_strict
        )
        transformation_map[p] = new_p
        if partial_warning:
            print(f"WARNING: Potential partial match in '{p}'. The replacements may not be isolated words.")
    return transformation_map


def check_for_conflicts(transformation_map: Dict[Path, Path]) -> bool:
    """
    Check for conflicts in the transformation map, i.e., multiple old paths
    mapping to the same new path. Returns True if conflicts exist, False if not.
    """
    seen = set()  # type: Set[Path]
    for new_p in transformation_map.values():
        if new_p in seen:
            return True
        seen.add(new_p)
    return False


def copy_item(
        src: Path,
        dst: Path,
        handle_symlinks: bool = False
) -> None:
    """
    Safely copy a file or a directory from src to dst.
    If handle_symlinks is True, copy symlinks as symlinks.
    Otherwise, copy the target file of the symlink.
    """
    if src.is_dir():
        shutil.copytree(
            src,
            dst,
            symlinks=handle_symlinks,
            dirs_exist_ok=True
        )
    else:
        dst.parent.mkdir(parents=True, exist_ok=True)
        if src.is_symlink() and handle_symlinks:
            link_target = os.readlink(src)
            os.symlink(link_target, dst)
        else:
            shutil.copy2(src.resolve() if src.is_symlink() else src, dst)


def validate_copy(
        src: Path,
        dst: Path,
        handle_symlinks: bool,
        rel_symlink_is_valid: bool = True
) -> bool:
    #TODO: needs to be tested, gives sometimes validations fails although files are copied correctly
    """
    Validate that the copied item at dst matches src.

    Args:
        src (Path): The source path.
        dst (Path): The destination path.
        handle_symlinks (bool): Indicates whether symlinks were copied as symlinks or not.
        rel_symlink_is_valid (bool): If True, identical symlink text (e.g., '../foo')
            is considered sufficient to declare the symlink valid. Defaults to True.

    Returns:
        bool: True if basic validation succeeds, False otherwise.
    """
    # If the destination doesn't exist at all, validation fails immediately.
    if not dst.exists():
        return False

    # Directory check: If src is a directory, confirm dst is a directory too.
    if src.is_dir():
        return dst.is_dir()

    # Symlink check:
    if src.is_symlink():
        # If we intentionally copy symlinks as symlinks...
        if handle_symlinks:
            # Check that the destination is also a symlink.
            if not dst.is_symlink():
                return False

            # If rel_symlink_is_valid is True, just compare the literal strings.
            if rel_symlink_is_valid:
                return os.readlink(src) == os.readlink(dst)
            else:
                # Otherwise, compare resolved absolute targets. This ensures both
                # symlinks actually point to the same real file/directory.
                return src.resolve() == dst.resolve()
        else:
            # If handle_symlinks=False, we copied the target's content instead of the symlink.
            # So validate that the destination file has the same size as the *target* of src.
            real_src = src.resolve()
            return real_src.stat().st_size == dst.stat().st_size

    # Regular file check: Just compare file sizes if both are normal files.
    return src.stat().st_size == dst.stat().st_size

def apply_transformations(
        transformation_map: Dict[Path, Path],
        dryrun: bool = True,
        handle_symlinks: bool = False,
        sequential_delete: bool = False
) -> None:
    """
    Apply the transformations from the transformation_map.

    Args:
        transformation_map (Dict[Path, Path]): Map of old paths to new paths.
        dryrun (bool): If True, only print actions. If False, actually copy.
        handle_symlinks (bool): If True, copy symlinks as symlinks. If False, copy their targets.
        sequential_delete (bool): If True, delete the original files after each successful copy and validation.
                                  Use with caution!
    """
    for src, dst in transformation_map.items():
        if dryrun:
            print(f"DRY RUN: Would copy {src} -> {dst}")
        else:
            try:
                copy_item(src, dst, handle_symlinks=handle_symlinks)
                # Validate copy
                if validate_copy(src, dst, handle_symlinks):
                    print(f"Copied {src} -> {dst}")
                    if sequential_delete:
                        # Double check before deleting source
                        if validate_copy(src, dst, handle_symlinks):
                            if src.is_dir():
                                shutil.rmtree(src)
                            else:
                                src.unlink()
                            print(f"Deleted original {src} after successful copy and validation.")
                        else:
                            print(f"Validation failed before delete for {src}. Not deleting.")
                else:
                    print(f"Validation failed for {src}. Destination {dst} may not match source.")
            except Exception as e:
                print(f"Error copying {src} to {dst}: {e}")


def plan_combine_folder_hierarchies(
        hierarchies: List[List[str]],
        root_dir: str = ".",
        securecopy_folder: Optional[str] = None
) -> Dict[Path, Path]:
    """
    Finds directories matching given hierarchies and plans to combine them.

    If securecopy_folder is provided, the new paths are placed under that folder within root_dir.
    """
    root = Path(root_dir)
    transformation_map = {}

    for hierarchy in hierarchies:
        if len(hierarchy) < 2:
            # No need to combine if only one folder name
            continue

        deepest_dir_name = hierarchy[-1]

        for found in root.rglob(deepest_dir_name):
            if found.is_dir():
                match = True
                parent = found
                for h in reversed(hierarchy):
                    if parent.name != h:
                        match = False
                        break
                    parent = parent.parent
                if match:
                    # Construct new combined name at the same level as the first folder in the hierarchy
                    combined_name = "_".join(hierarchy)
                    original_dir = parent.joinpath(*hierarchy)
                    new_dir = parent / combined_name

                    if securecopy_folder is not None:
                        # Place under securecopy folder
                        relative_path = new_dir.relative_to(root)
                        new_dir = root.joinpath(securecopy_folder, relative_path)

                    transformation_map[original_dir] = new_dir

    return transformation_map



def plan_split_folder_hierarchies(
        combined_folders: List[str],
        root_dir: str = ".",
        securecopy_folder: Optional[str] = None
) -> Dict[Path, Path]:
    """
    Finds directories that match combined patterns and splits them back into hierarchies.
    If securecopy_folder is provided, the new paths are placed under that folder within root_dir.
    """
    root = Path(root_dir)
    transformation_map = {}

    for combined in combined_folders:
        parts = combined.split("_")
        if len(parts) < 2:
            # No split needed
            continue

        for found in root.rglob(combined):
            if found.is_dir():
                parent = found.parent
                target = parent
                for p in parts:
                    target = target / p

                if securecopy_folder is not None:
                    # Place under securecopy folder
                    relative_path = target.relative_to(root)
                    target = root.joinpath(securecopy_folder, relative_path)

                transformation_map[found] = target

    return transformation_map

## Caution, not sure if this already works as intended, needs mor testing
def plan_prepend_foldernames_to_filename(
        file_paths: List[str],
        foldernames: List[str],
        folderremoval: bool = True,
        root_dir: str = ".",
        securecopy_folder: Optional[str] = None
) -> Dict[Path, Path]:
    """
    Prepend given folder names to each file's basename, optionally removing these folders from the directory path,
    but only if all given folder names appear in the original path.

    If folderremoval=True and all foldernames are present:
        e.g. foldernames=["bla1","bla3"]
        original: bla1/bla2/bla3/bla4/test.txt
        transformed: bla2/bla4/bla1_bla3_test.txt

    If folderremoval=False and all foldernames are present:
        original: bla1/bla2/bla3/bla4/test.txt
        transformed: bla1/bla2/bla3/bla4/bla1_bla3_test.txt

    If not all foldernames are present, no change is applied.

    If securecopy_folder is provided, the new paths are placed under that folder within root_dir.
    """
    transformation_map = {}
    folder_set = set(foldernames)
    prepend_str = "_".join(foldernames)
    root_path = Path(root_dir)

    for fp in file_paths:
        p = Path(fp)
        # Ensure absolute path relative to root_dir
        abs_p = (root_path / p).resolve()
        filename = abs_p.name
        parent_parts = list(abs_p.parent.relative_to(root_path).parts)

        # Check if all foldernames are present in the path
        # This ensures we only transform if the path actually contains all specified folders
        if all(fn in parent_parts for fn in foldernames):
            # All foldernames found
            if folderremoval:
                # Remove the folders from the path
                new_parent_parts = [part for part in parent_parts if part not in folder_set]
                parent_parts = new_parent_parts

            # Prepend foldernames to the filename
            new_filename = f"{prepend_str}_{filename}"
        else:
            # Not all foldernames found, no change to the file name
            new_filename = filename

        new_path = Path(*parent_parts) / new_filename

        if securecopy_folder is not None:
            new_path = root_path.joinpath(securecopy_folder, new_path)

        transformation_map[abs_p] = new_path

    return transformation_map


def build_transformation_map_from_df(
    df: pd.DataFrame,
    base_dir: str,
    key_field: str = 'recording_id',
    rename_format: str = 'task-{task_id}_run-{run_id}',
    target_directory: Optional[str] = None,
    include_non_matches: bool = True  # New argument
) -> Dict[Path, Path]:
    """
    Build a transformation map from a DataFrame that maps original file paths to new file paths,
    by replacing a directory named after `key_field` with a new name derived from `rename_format`.

    Args:
        df (pd.DataFrame): DataFrame with at least `key_field` and fields required by `rename_format`.
        base_dir (str): Base directory containing the original file structure.
        key_field (str): Field identifying the directory to rename (default: 'recording_id').
        rename_format (str): A format string with placeholders (e.g. 'task-{task_id}_run-{run_id}').
        target_directory (Optional[str]): If provided, transformed directories and files go here.
                                          Otherwise, a 'securecopy' folder under `base_dir` is used.
        include_non_matches (bool): If True, include files that do not match the key_field "as is".

    Returns:
        Dict[Path, Path]: A mapping of original paths -> new paths.
    """
    base_path = Path(base_dir)
    if target_directory is not None:
        target_path = Path(target_directory)
    else:
        target_path = base_path / "securecopy"

    if key_field not in df.columns:
        logging.warning("Key field '%s' not in DataFrame. Cannot build transformation map.", key_field)
        return {}

    # Collect all files from base_dir
    all_files = get_file_list(str(base_path), omit_hidden=True)

    # Extract placeholders from rename_format
    placeholders = re.findall(r'{([^}]+)}', rename_format)

    transformation_map = {}

    # Build transformations for each record
    matched_files = set()
    for _, row in df.iterrows():
        recording_id = str(row[key_field])

        # Gather rename values
        rename_values = {}
        missing_placeholder = False
        for ph in placeholders:
            val = row.get(ph)
            if val is None:
                logging.warning("Missing value for placeholder '%s' in record '%s'. Skipping this record.", ph, recording_id)
                missing_placeholder = True
                break
            rename_values[ph] = sanitize_filename(str(val))

        if missing_placeholder:
            continue

        new_name = rename_format.format(**rename_values)

        # For all files that contain recording_id as a directory component:
        # Replace that component with new_name, preserving the rest
        for original_file in all_files:
            relative_path = original_file.relative_to(base_path)
            parts = list(relative_path.parts)

            if recording_id in parts:
                # Replace the directory corresponding to the recording_id
                new_parts = [new_name if p == recording_id else p for p in parts]
                # Construct the new path under target_path
                new_path = target_path.joinpath(*new_parts)

                if new_path in transformation_map.values():
                    logging.warning("Duplicate target path encountered: %s. Skipping this file to avoid conflict.", new_path)
                    continue

                transformation_map[original_file] = new_path
                matched_files.add(original_file)

    # Handle non-matching files if include_non_matches is True
    if include_non_matches:
        for original_file in all_files:
            if original_file not in matched_files:
                # Copy non-matching files "as is" to the target directory
                relative_path = original_file.relative_to(base_path)
                new_path = target_path / relative_path
                if new_path in transformation_map.values():
                    logging.warning("Duplicate target path for non-matching file: %s. Skipping to avoid conflict.", new_path)
                    continue
                transformation_map[original_file] = new_path

    # Check for conflicts in the completed map
    if check_for_conflicts(transformation_map):
        logging.error("Conflicts detected in transformation map. Returning empty map.")
        return {}

    return transformation_map




def plan_complex_file_reorder(
    base_dir: str,
    source_structure: List[str],
    target_index: List[int],
    securecopy_folder: str = "securecopy",
    target_dir: Optional[str] = None
) -> Dict[Path, Path]:
    """
    Builds a transformation map for files only, ignoring directories.
    Reorders each file's parent folder segments according to source_structure,
    then places the file in the new location under target_dir (or securecopy_folder).

    We do NOT physically descend into '.git' or 'git annex' directories,
    but if a symlink outside those folders points into them, it is processed normally.

    Args:
        base_dir (str):
            The root directory where we locate files.
        source_structure (List[str]):
            Blueprint for how folders are currently arranged. E.g.:
               ["^sub-[a-zA-Z0-9]+$", "^dyad-[a-zA-Z0-9]+$", "<subfolders>"]
        target_index (List[int]):
            A human-friendly list (starting at 1) specifying how to reorder
            the placeholders in source_structure. Example: [2, 3, 1].
        securecopy_folder (str):
            If target_dir is not provided, place outputs here under base_dir.
        target_dir (Optional[str]):
            An explicit destination directory. If given, overrides securecopy_folder.

    Returns:
        Dict[Path, Path]:
            Mapping of old_path -> new_path for all files that match the structure.
            Others are omitted.
    """
    base_path = Path(base_dir).resolve()

    # Determine the reorder root
    if target_dir:
        reorder_root = Path(target_dir).resolve()
    else:
        reorder_root = base_path / securecopy_folder

    transformation_map = {}

    # 1) Collect files only
    all_files = []
    for root, dirs, files in os.walk(base_path):
        root_path = Path(root)

        # --- Skip physically descending into .git or 'git annex' folders ---
        # If you have more variants (e.g. 'git-annex' vs 'git annex') adapt below.
        dirs[:] = [
            d for d in dirs
            if d not in ('.git', 'git annex')
        ]

        # Now gather files from the current folder
        for f in files:
            file_path = root_path / f
            # It's enough to check if it's a file or symlink; either way, we handle it
            # as a "file" for our transformation purposes.
            if file_path.is_file() or file_path.is_symlink():
                all_files.append(file_path)

    # 2) Convert target_index from 1-based to 0-based
    zero_based_index = [i - 1 for i in target_index]

    # 3) Build a transformation map for each file
    for old_path in all_files:
        # Skip if old_path is inside reorder_root (avoid recursion or re-copying)
        if reorder_root in old_path.parents:
            continue

        # Build the relative folder parts (excluding the file name)
        relative = old_path.relative_to(base_path)
        parts = list(relative.parts)

        if not parts:
            # Edge case: somehow the file is base_dir itself? skip
            continue

        filename = parts[-1]          # last part is the file name (or symlink name)
        folder_parts = parts[:-1]     # everything before that is the folder chain

        # Reorder the folder chain
        new_folder_parts = reorder_path_complex(folder_parts, source_structure, zero_based_index)
        if new_folder_parts is None:
            # parse/match failure => skip
            continue

        # Build final path (append the filename at the end)
        new_parts = new_folder_parts + [filename]
        new_path = reorder_root.joinpath(*new_parts)

        # Add to transformation map
        transformation_map[old_path] = new_path

    return transformation_map


def reorder_path_complex(
    folder_parts: List[str],
    source_structure: List[str],
    target_index: List[int]
) -> Optional[List[str]]:
    """
    Reorder path segments (folder_parts) according to source_structure + target_index.
    Returns None if matching fails.

    Example:
        folder_parts = ["sub-01A", "dyad-02", "task-conversation_run-01"]
        source_structure = ["^sub-[a-zA-Z0-9]+$", "^dyad-[a-zA-Z0-9]+", "<subfolders>"]
        target_index = [1, 2, 0]  # zero-based => placeholders #1, #2, #0 in that order

    This might reorder to: ["dyad-02", "task-conversation_run-01", "sub-01A"].
    """
    captures = {}
    placeholders_in_source = []
    idx = 0

    # 1) Parse placeholders
    for i, placeholder in enumerate(source_structure):
        placeholders_in_source.append(placeholder)

        if placeholder.startswith("<") and placeholder.endswith(">"):
            # wildcard captures everything until the next regex
            next_idx = find_next_pattern_index(source_structure, i + 1, folder_parts, idx)
            captures[placeholder] = folder_parts[idx:next_idx]
            idx = next_idx
        else:
            # regex placeholder => match exactly one segment
            if idx >= len(folder_parts):
                return None  # not enough segments
            pattern = re.compile(placeholder)
            part = folder_parts[idx]
            if not pattern.match(part):
                return None  # mismatch
            captures[placeholder] = [part]
            idx += 1

    # leftover
    leftover = folder_parts[idx:]
    if leftover:
        last_ph = source_structure[-1]
        if last_ph.startswith("<") and last_ph.endswith(">"):
            captures[last_ph].extend(leftover)
        else:
            return None  # leftover with no wildcard

    # 2) Reassemble in the order specified by target_index
    new_parts = []
    # placeholders_in_source has same length as source_structure
    for idx_ in target_index:
        if idx_ < 0 or idx_ >= len(placeholders_in_source):
            return None
        ph = placeholders_in_source[idx_]
        segs = captures.get(ph, [])
        new_parts.extend(segs)

    return new_parts


def find_next_pattern_index(
    source_structure: List[str],
    start_idx: int,
    folder_parts: List[str],
    current_part_index: int
) -> int:
    """
    Find the next position in folder_parts that matches a regex placeholder
    in source_structure, starting at start_idx. Return len(folder_parts) if none is found.
    """
    next_pattern = None
    for placeholder in source_structure[start_idx:]:
        if not (placeholder.startswith("<") and placeholder.endswith(">")):
            next_pattern = placeholder
            break

    if next_pattern is None:
        # no more regex => wildcard grabs everything
        return len(folder_parts)

    pattern = re.compile(next_pattern)
    for i in range(current_part_index, len(folder_parts)):
        if pattern.match(folder_parts[i]):
            return i
    return len(folder_parts)