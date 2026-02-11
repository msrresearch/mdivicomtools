# mdivicomtools/__init__.py


from typing import List, Optional

from .utils.rename import (
    get_file_list,
    plan_transformations,
    check_for_conflicts,
    apply_transformations,
    plan_combine_folder_hierarchies,
    plan_split_folder_hierarchies,
    plan_prepend_foldernames_to_filename,
    copy_item,
    sanitize_filename
)

# split folders and folders2files still needs to be tested!

def vc_rename(base_dir,
              find_strings,
              replace_strings,
              prefix,
              securecopy_folder="transformed",
              partial_strict=True,
              dryrun=True,
              handle_symlinks=True,
              sequential_delete=False):
    """
    Rename files in a directory using a find/replace scheme.

    This function retrieves all files in the specified directory, applies a string find/replace
    transformation with an optional prefix, and moves the files under a secure copy folder structure.
    Conflicts are checked before any actual file copying occurs.

    Args:
        base_dir (str): The root directory containing the files to transform.
        find_strings (List[str]): A list of strings to search for in the file paths.
        replace_strings (Optional[List[str]]): A list of replacement strings corresponding to each find string.
        prefix (str): A prefix to prepend to matched strings or replacements.
        securecopy_folder (str, optional): The name of the folder where transformed files are placed. Defaults to "transformed".
        partial_strict (bool, optional): If True, only replaces exact word-boundary matches. Defaults to True.
        dryrun (bool, optional): If True, prints the planned actions without applying them. Defaults to True.
        handle_symlinks (bool, optional): Whether to preserve symlinks during the transformation. Defaults to True.
        sequential_delete (bool, optional): If True, deletes the source file after a successful copy. Use with caution. Defaults to False.
                                            WARNING: Enabling this option will permanently delete the source files upon successful transformation.
                                            Ensure you have proper backups before proceeding. Defaults to False.
    Returns:
        Dict[Path, Path]: A mapping of original file paths to their transformed paths.
    """
    files = get_file_list(base_dir)
    transformation_map = plan_transformations(
        base_dir,
        files,
        find_strings,
        replace_strings,
        prefix,
        partial_strict=partial_strict,
        securecopy_folder=securecopy_folder
    )
    if check_for_conflicts(transformation_map):
        print("Conflicts detected! Aborting.")
    else:
        apply_transformations(
            transformation_map,
            dryrun=dryrun,
            handle_symlinks=handle_symlinks,
            sequential_delete=sequential_delete
        )
        if dryrun:
            print("Dry run completed. No files were modified. Use dryrun=False to apply transformations.")
    return transformation_map

def vc_combine_folder(hierarchies,
                      root_dir=".",
                      securecopy_folder: Optional[str] = None,
                      dryrun=True,
                      handle_symlinks=True,
                      sequential_delete=False):
    """
    Combine multiple folder hierarchies into single-level folders.

    This function identifies directories that match specified folder hierarchies and combines
    them into single-level directories within the defined secure copy folder. It then applies
    the transformation by copying files into the new folder structure after checking for conflicts.

    Args:
        hierarchies (List[List[str]]): A list of folder hierarchies. Each hierarchy is defined as a list of folder names.
        root_dir (str, optional): The root directory to search for folder hierarchies. Defaults to ".".
        securecopy_folder (Optional[str]): Optional secure copy folder under root_dir where the transformed structure is placed.
        dryrun (bool, optional): If True, prints the planned actions without applying them. Defaults to True.
        handle_symlinks (bool, optional): Whether to preserve symlinks during the transformation. Defaults to True.
        sequential_delete (bool, optional): If True, deletes the source after a successful transformation. Defaults to False.
                                            WARNING: Enabling this option will permanently delete the source folders upon successful transformation.
                                            Ensure you have proper backups before proceeding. Defaults to False.

    Returns:
        Dict[Path, Path]: A mapping of original folder paths to their new combined folder paths.
    """
    transformation_map = plan_combine_folder_hierarchies(hierarchies, root_dir=root_dir, securecopy_folder=securecopy_folder)
    if check_for_conflicts(transformation_map):
        print("Conflicts detected! Aborting.")
    else:
        apply_transformations(
            transformation_map,
            dryrun=dryrun,
            handle_symlinks=handle_symlinks,
            sequential_delete=sequential_delete
        )
        if dryrun:
            print("Dry run completed. Use dryrun=False to apply transformations.")
    return transformation_map


def vc_split_folder(combined_folders,
                    root_dir=".",
                    securecopy_folder: Optional[str] = None,
                    dryrun=True,
                    handle_symlinks=True,
                    sequential_delete=False):
    """
    Split previously combined folders back into hierarchical folder structures.

    This function takes folder names that were previously combined into a single directory name and splits
    them into their original hierarchical structure under the secure copy folder or specified directory.
    The function verifies for conflicts before applying the transformation.

    Args:
        combined_folders (List[str]): A list of folder names that represent the combined directories.
        root_dir (str, optional): The base directory to search for the combined folders. Defaults to ".".
        securecopy_folder (Optional[str]): Optional secure copy folder under root_dir where the split folders are placed.
        dryrun (bool, optional): If True, prints the planned actions without applying them. Defaults to True.
        handle_symlinks (bool, optional): Whether to preserve symlinks during the transformation. Defaults to True.
        sequential_delete (bool, optional): If True, deletes the source after a successful transformation. Defaults to False.
                                            WARNING: Enabling this option will permanently delete the source folders upon successful transformation.
                                            Ensure you have proper backups before proceeding. Defaults to False.

    Returns:
        Dict[Path, Path]: A mapping of original combined folder paths to their new hierarchical folder paths.
    """
    transformation_map = plan_split_folder_hierarchies(combined_folders, root_dir=root_dir, securecopy_folder=securecopy_folder)
    if check_for_conflicts(transformation_map):
        print("Conflicts detected! Aborting.")
    else:
        apply_transformations(
            transformation_map,
            dryrun=dryrun,
            handle_symlinks=handle_symlinks,
            sequential_delete=sequential_delete
        )
        if dryrun:
            print("Dry run completed. Use dryrun=False to apply transformations.")
    return transformation_map


def vc_folder2files(file_paths,
                    foldernames,
                    folderremoval=True,
                    root_dir=".",
                    securecopy_folder: Optional[str] = None,
                    dryrun=True,
                    handle_symlinks=True,
                    sequential_delete=False):
    """
    Prepend specific folder names to filenames, optionally removing the original folder structure.

    This function examines each file path and, if all specified folder names are present in the path,
    prepends them to the filename. Optionally, the folder names can be removed from the directory path.
    The transformed files are placed under a secure copy folder if specified.

    Args:
        file_paths (List[str]): A list of file paths to be processed.
        foldernames (List[str]): A list of folder names to search for in each file's path.
        folderremoval (bool, optional): If True, removes the specified folder names from the path before renaming. Defaults to True.
        root_dir (str, optional): The base directory from which file paths are resolved. Defaults to ".".
        securecopy_folder (Optional[str]): Optional secure copy folder under root_dir where the transformed files will be placed.
        dryrun (bool, optional): If True, prints the planned actions without applying them. Defaults to True.
        handle_symlinks (bool, optional): Whether to preserve symlinks during the transformation. Defaults to True.
        sequential_delete (bool, optional): If True, deletes the source file after a successful transformation. Defaults to False.
                                            WARNING: Enabling this option will permanently delete the source folders upon successful transformation.
                                            Ensure you have proper backups before proceeding. Defaults to False.

    Returns:
        Dict[Path, Path]: A mapping of original file paths to their transformed file paths.
    """
    transformation_map = plan_prepend_foldernames_to_filename(
        file_paths=file_paths,
        foldernames=foldernames,
        folderremoval=folderremoval,
        root_dir=root_dir,
        securecopy_folder=securecopy_folder
    )

    if check_for_conflicts(transformation_map):
        print("Conflicts detected! Aborting.")
    else:
        apply_transformations(
            transformation_map,
            dryrun=dryrun,
            handle_symlinks=handle_symlinks,
            sequential_delete=sequential_delete
        )
        if dryrun:
            print("Dry run completed. Use dryrun=False to apply transformations.")
    return transformation_map
