# templ_heroicons_generator/core/scanner.py

import os
import re
# import sys # No longer needed if sys.exit is removed
from typing import List, Dict, Set

from .icons import Icon, extract_icon_details
from . import config # For ICON_USAGE_PATTERN


def find_used_icons(
    input_dir: str,
    output_dir_to_exclude: str,
    exclude_output_dir_files: bool,
    verbose: bool,
    valid_icons_list: Dict[str, List[str]]
) -> List[Icon]:
    """
    Scans .templ files recursively in the input directory to find used Heroicons.

    It identifies icon usages matching the configured pattern (typically
    "@heroicons.Style_icon_name"), validates them against the fetched list of known
    Heroicons (if available), and creates Icon objects for valid usages.

    Args:
        input_dir: The root directory of the project to scan for .templ files.
        output_dir_to_exclude: The directory whose .templ files should be excluded
                               from scanning if `exclude_output_dir_files` is True.
        exclude_output_dir_files: If True, .templ files within `output_dir_to_exclude`
                                  will not be scanned.
        verbose: If True, prints detailed logs during the scanning process.
        valid_icons_list: A dictionary mapping icon styles ('outline', 'solid')
                          to lists of known icon file names. Used for validation.
                          If empty or None, remote validation is effectively skipped.

    Returns:
        A list of unique `Icon` objects representing the valid Heroicons found,
        sorted by component name.

    Raises:
        FileNotFoundError: If the `input_dir` does not exist or is not a directory.
    """
    if not os.path.isdir(input_dir):
        raise FileNotFoundError(f"Input directory '{input_dir}' not found or is not a directory.")

    abs_input_dir = os.path.abspath(input_dir)
    abs_output_dir_to_exclude = os.path.abspath(os.path.join(input_dir, output_dir_to_exclude)) \
        if not os.path.isabs(output_dir_to_exclude) else os.path.abspath(output_dir_to_exclude)

    icon_pattern = re.compile(config.ICON_USAGE_PATTERN)
    found_icons_dict: Dict[str, Icon] = {} # Key: raw_component_name, Value: Icon object
    templ_files_to_scan: List[str] = []

    if verbose:
        print(f"Scanning for .templ files in '{abs_input_dir}'...")
        if exclude_output_dir_files:
            print(f"  Excluding scans within: '{abs_output_dir_to_exclude}'")

    for root, _, files in os.walk(abs_input_dir):
        current_abs_root = os.path.abspath(root)
        if exclude_output_dir_files:
            if current_abs_root == abs_output_dir_to_exclude or \
               current_abs_root.startswith(abs_output_dir_to_exclude + os.sep):
                if verbose:
                    # Use os.path.relpath for cleaner output if abs_input_dir is a parent
                    try:
                        rel_skipped_path = os.path.relpath(current_abs_root, abs_input_dir)
                    except ValueError: # current_abs_root might not be under abs_input_dir (e.g. different drives on Windows)
                        rel_skipped_path = current_abs_root
                    print(f"  Skipping directory: {rel_skipped_path}")
                continue
        for file_name in files:
            if file_name.endswith(".templ"):
                templ_files_to_scan.append(os.path.join(current_abs_root, file_name))

    if not templ_files_to_scan:
        if verbose:
            print("No .templ files found in the specified input directory (excluding output directory if applicable).")
        return []

    if verbose:
        print(f"Analyzing {len(templ_files_to_scan)} .templ file(s)...")

    files_with_read_errors = 0
    total_references_found = 0
    unique_raw_names_found: Set[str] = set()

    for file_path in templ_files_to_scan:
        # Use os.path.relpath for cleaner output if abs_input_dir is a parent
        try:
            relative_file_path = os.path.relpath(file_path, abs_input_dir)
        except ValueError:
            relative_file_path = file_path

        if verbose:
            print(f"  - Analyzing: {relative_file_path}")
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            matches = icon_pattern.findall(content)
            # Example for verbosity levels using an environment variable (can be adapted)
            # This requires cli.py to potentially set this if using args.verbose count
            verbose_level = 0
            if verbose: # Base verbosity
                verbose_level = 1
            if os.environ.get("VERBOSE_LEVEL") and os.environ.get("VERBOSE_LEVEL", "0").isdigit():
                 verbose_level = max(verbose_level, int(os.environ.get("VERBOSE_LEVEL", "0")))


            if not matches and verbose_level > 1:
                 print(f"    No heroicon patterns found in {relative_file_path}.")

            for raw_component_name in matches:
                total_references_found += 1
                unique_raw_names_found.add(raw_component_name)

                if raw_component_name in found_icons_dict:
                    continue

                icon_details = extract_icon_details(raw_component_name)
                if icon_details:
                    svg_file_name, style, go_component_name = icon_details

                    is_known_icon = True
                    if valid_icons_list:
                        if style in valid_icons_list:
                            if svg_file_name not in valid_icons_list[style]:
                                is_known_icon = False
                                if verbose: # This level of detail is good for standard verbose
                                    print(f"    Warning: Icon '@heroicons.{raw_component_name}' in {relative_file_path} "
                                          f"resolved to '{svg_file_name}.svg' ({style}), which is not a known icon. Skipping.") # Removed file=sys.stderr
                        else:
                            is_known_icon = False
                            if verbose:
                                print(f"    Warning: Style '{style}' for '@heroicons.{raw_component_name}' in {relative_file_path} "
                                      f"not found in fetched icon lists. Skipping.") # Removed file=sys.stderr

                    if is_known_icon:
                        found_icons_dict[raw_component_name] = Icon(go_component_name, svg_file_name, style)
                        if verbose:
                            print(f"    Found valid icon usage: {go_component_name} (Style: {style}, File: {svg_file_name}.svg)")
                elif verbose:
                    print(f"    Warning: Could not parse icon details for '@heroicons.{raw_component_name}' in {relative_file_path}. "
                          f"Ensure format is Style_icon_name (e.g., Outline_bars_3).") # Removed file=sys.stderr

        except FileNotFoundError: # Should be rare given os.walk, but good practice
            if verbose:
                print(f"  Error: File not found during analysis {relative_file_path}. It might have been moved or deleted.") # Removed file=sys.stderr
            files_with_read_errors += 1
        except Exception as e: # Catch other read/processing errors
            if verbose:
                print(f"  Error reading or processing file {relative_file_path}: {e}") # Removed file=sys.stderr
            files_with_read_errors += 1

    if files_with_read_errors > 0 and verbose:
        print(f"Warning: Encountered errors while reading {files_with_read_errors} file(s). Results might be incomplete.") # Removed file=sys.stderr

    final_icons_list = sorted(list(found_icons_dict.values()), key=lambda x: x.component_name)

    if verbose: # This summary block is good for standard verbose
        total_unique_raw_refs = len(unique_raw_names_found)
        valid_unique_icons_count = len(final_icons_list)
        if final_icons_list:
            print(f"Found {valid_unique_icons_count} unique valid Heroicons to generate "
                  f"(from {total_unique_raw_refs} unique raw references across {total_references_found} total usages):")
            # Use the verbose_level defined earlier, or simplify if preferred
            if verbose_level <= 1 :
                names = [icon.component_name for icon in final_icons_list[:10]]
                print(f"    [{', '.join(names)}{'...' if len(final_icons_list) > 10 else ''}]")
            else: # Higher verbosity
                for icon in final_icons_list:
                    print(f"    - {icon.component_name} (Style: {icon.style}, File: {icon.file_name}.svg)")
        elif templ_files_to_scan:
             print(f"No valid Heroicons usage matching the format '@heroicons.Style_icon_name' found "
                   f"in the scanned files (Total raw references: {total_references_found}, "
                   f"Unique raw references: {total_unique_raw_refs}).")

        skipped_count = total_unique_raw_refs - valid_unique_icons_count
        if skipped_count > 0:
            print(f"Note: {skipped_count} unique icon reference(s) were skipped due to parsing errors or failed validation (see warnings above).")

    return final_icons_list