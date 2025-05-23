# templ_heroicons_generator/core/scanner.py

import os
import re
import sys
from typing import List, Dict, Set

from .icons import Icon, extract_icon_details
from . import config


def find_used_icons(
    input_dir: str,
    output_dir_to_exclude: str,  # This is the raw value from args.output_dir
    exclude_output_dir_files: bool,
    verbose: bool,
    silent: bool,
    valid_icons_list: Dict[str, List[str]],
) -> List[Icon]:
    """
    Scans .templ files recursively in the input directory to find used Heroicons,
    excluding the specified output directory if it falls within the input directory.

    It identifies icon usages matching the configured pattern (typically
    "@heroicons.Style_icon_name"), validates them against the fetched list of known
    Heroicons (if available), and creates Icon objects for valid usages.
    If verbose mode is enabled (and not silent), it lists all files crawled.

    Args:
        input_dir: The root directory of the project to scan for .templ files (resolved from CWD).
        output_dir_to_exclude: The output directory path (resolved from CWD) to exclude from scanning.
        exclude_output_dir_files: If True, .templ files within `output_dir_to_exclude`
                                  will not be scanned.
        verbose: If True (and silent is False), prints detailed logs, including crawled files.
        silent: If True, suppresses all informational output except critical errors.
        valid_icons_list: A dictionary mapping icon styles ('outline', 'solid')
                          to lists of known icon file names. Used for validation.
                          If empty or None, remote validation is effectively skipped.

    Returns:
        A list of unique `Icon` objects representing the valid Heroicons found,
        sorted by component name.

    Raises:
        FileNotFoundError: If the `input_dir` does not exist or is not a directory.
    """
    if not os.path.isdir(
        input_dir
    ):  # input_dir is already absolute if called from cli.py as os.path.abspath(args.input_dir)
        # or it's resolved from CWD if passed directly.
        # For robustness, ensure it's absolute here or before.
        # Let's assume cli.py does not make it absolute, and resolve it here.
        input_dir_abs_path = os.path.abspath(input_dir)
        if not os.path.isdir(input_dir_abs_path):
            raise FileNotFoundError(
                f"Input directory '{input_dir}' (resolved to '{input_dir_abs_path}') not found or is not a directory."
            )
    else:
        input_dir_abs_path = os.path.abspath(input_dir)

    # output_dir_to_exclude is also resolved from CWD by making it absolute directly.
    # This ensures it's independent of input_dir's path structure unless explicitly made relative to it by the user.
    abs_output_dir_to_exclude = os.path.abspath(output_dir_to_exclude)

    icon_pattern = re.compile(config.ICON_USAGE_PATTERN)
    found_icons_dict: Dict[str, Icon] = {}
    templ_files_to_scan: List[str] = []
    all_crawled_files_count = 0

    verbose_level = 0
    if verbose:
        verbose_level = 1
    env_verbose_level_str = os.environ.get("VERBOSE_LEVEL")
    if env_verbose_level_str and env_verbose_level_str.isdigit():
        verbose_level = max(verbose_level, int(env_verbose_level_str))

    if verbose:
        print(f"Scanning for .templ files in '{input_dir_abs_path}'...")
        if exclude_output_dir_files:
            # For clarity, show what abs_output_dir_to_exclude resolved to
            print(
                f"  Excluding scans within output directory: '{abs_output_dir_to_exclude}' (if it's under input dir)"
            )

    for root, dirs, files in os.walk(
        input_dir_abs_path
    ):  # Walk the absolute input path
        current_abs_root = os.path.abspath(
            root
        )  # root from os.walk is already absolute if top is absolute

        if verbose:
            try:
                rel_current_root = os.path.relpath(current_abs_root, input_dir_abs_path)
            except ValueError:
                rel_current_root = current_abs_root
            # Handle case where rel_current_root is '.' for the top input_dir_abs_path itself
            print(
                f"  Crawling directory: {rel_current_root if rel_current_root != '.' else input_dir_abs_path}"
            )

        if exclude_output_dir_files:
            # Check if current_abs_root is identical to or a subdirectory of abs_output_dir_to_exclude
            # This correctly handles cases where output_dir might be outside, inside, or identical to input_dir.
            # We only care about exclusion if current_abs_root is *within* the scan path that started from input_dir_abs_path
            # AND it matches the output directory.
            if (
                current_abs_root == abs_output_dir_to_exclude
                or current_abs_root.startswith(abs_output_dir_to_exclude + os.sep)
            ):
                if verbose:
                    # Path for logging should be relative to input_dir_abs_path for clarity
                    log_skipped_path = (
                        os.path.relpath(current_abs_root, input_dir_abs_path)
                        if current_abs_root.startswith(input_dir_abs_path)
                        else current_abs_root
                    )
                    print(f"    Skipping excluded directory: {log_skipped_path}")
                dirs[:] = []
                continue

        for file_name in files:
            all_crawled_files_count += 1
            file_path = os.path.join(current_abs_root, file_name)
            if verbose:
                try:
                    rel_file_path_crawl = os.path.relpath(file_path, input_dir_abs_path)
                except ValueError:
                    rel_file_path_crawl = file_path
                print(f"    Found file: {rel_file_path_crawl}")

            if file_name.endswith(".templ"):
                # Ensure we are not adding files from an excluded output directory
                # This is a secondary check, primarily handled by pruning `dirs`.
                # This handles the case where output_dir_to_exclude is the input_dir itself.
                if exclude_output_dir_files and (
                    current_abs_root == abs_output_dir_to_exclude
                    or current_abs_root.startswith(abs_output_dir_to_exclude + os.sep)
                ):
                    # This file is in the root of the excluded dir, which wasn't pruned if it's the top dir.
                    if verbose and file_name.endswith(".templ"):
                        print(
                            f"    Skipping .templ file in excluded output directory root: {os.path.relpath(file_path, input_dir_abs_path)}"
                        )
                    continue
                templ_files_to_scan.append(file_path)

    if not templ_files_to_scan:
        if verbose:
            print(
                f"No .templ files found to analyze in '{input_dir_abs_path}' (out of {all_crawled_files_count} files crawled, respecting exclusions)."
            )
        elif not silent:
            print(
                f"No .templ files found to analyze (scanned {all_crawled_files_count} files, respecting exclusions)."
            )
        return []

    if verbose:
        print(
            f"Analyzing {len(templ_files_to_scan)} .templ file(s) (from {input_dir_abs_path}, {all_crawled_files_count} files crawled total)..."
        )
    elif not silent:
        print(f"Analyzing {len(templ_files_to_scan)} .templ file(s)...")

    files_with_read_errors = 0
    total_references_found = 0
    unique_raw_names_found: Set[str] = set()

    for file_path in templ_files_to_scan:
        try:
            relative_file_path = os.path.relpath(file_path, input_dir_abs_path)
        except ValueError:
            relative_file_path = (
                file_path  # Should not happen if file_path is under input_dir_abs_path
            )

        if verbose:
            print(f"  - Analyzing .templ file: {relative_file_path}")
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            matches = icon_pattern.findall(content)

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
                                if verbose:
                                    print(
                                        f"    Warning: Icon '@heroicons.{raw_component_name}' in {relative_file_path} "
                                        f"resolved to '{svg_file_name}.svg' ({style}), which is not a known icon. Skipping.",
                                        file=sys.stderr,
                                    )
                        else:
                            is_known_icon = False
                            if verbose:
                                print(
                                    f"    Warning: Style '{style}' for '@heroicons.{raw_component_name}' in {relative_file_path} "
                                    f"not found in fetched icon lists (available styles: {list(valid_icons_list.keys())}). Skipping.",
                                    file=sys.stderr,
                                )

                    if is_known_icon:
                        found_icons_dict[raw_component_name] = Icon(
                            go_component_name, svg_file_name, style
                        )
                        if verbose:
                            print(
                                f"    Found valid icon usage: {go_component_name} (Style: {style}, File: {svg_file_name}.svg)"
                            )
                elif verbose:
                    print(
                        f"    Warning: Could not parse icon details for '@heroicons.{raw_component_name}' in {relative_file_path}. "
                        f"Ensure format is Style_icon_name (e.g., Outline_bars_3).",
                        file=sys.stderr,
                    )

        except FileNotFoundError:  # Should be rare due to os.walk
            if verbose:
                print(
                    f"  Error: File not found during analysis {relative_file_path}. It might have been moved or deleted.",
                    file=sys.stderr,
                )
            files_with_read_errors += 1
        except Exception as e:
            if verbose:
                print(
                    f"  Error reading or processing file {relative_file_path}: {e}",
                    file=sys.stderr,
                )
            files_with_read_errors += 1

    if files_with_read_errors > 0 and verbose:
        print(
            f"Warning: Encountered errors while reading {files_with_read_errors} file(s). Results might be incomplete.",
            file=sys.stderr,
        )

    final_icons_list = sorted(
        list(found_icons_dict.values()), key=lambda x: x.component_name
    )

    if verbose:
        total_unique_raw_refs = len(unique_raw_names_found)
        valid_unique_icons_count = len(final_icons_list)
        if final_icons_list:
            print(
                f"Found {valid_unique_icons_count} unique valid Heroicons to generate "
                f"(from {total_unique_raw_refs} unique raw references across {total_references_found} total usages):"
            )
            if verbose_level <= 1:
                names = [icon.component_name for icon in final_icons_list[:10]]
                print(
                    f"    [{', '.join(names)}{'...' if len(final_icons_list) > 10 else ''}]"
                )
            else:
                for icon in final_icons_list:
                    print(
                        f"    - {icon.component_name} (Style: {icon.style}, File: {icon.file_name}.svg)"
                    )
        elif (
            templ_files_to_scan or all_crawled_files_count > 0
        ):  # Check if any files were scanned or crawled
            print(
                f"No valid Heroicons usage matching the format '@heroicons.Style_icon_name' found "
                f"in the scanned .templ files (Total raw references: {total_references_found}, "
                f"Unique raw references: {total_unique_raw_refs})."
            )

        skipped_count = total_unique_raw_refs - valid_unique_icons_count
        if skipped_count > 0:
            print(
                f"Note: {skipped_count} unique icon reference(s) were skipped due to parsing errors or failed validation (see warnings above)."
            )
    elif (
        not silent
        and not final_icons_list
        and (templ_files_to_scan or all_crawled_files_count > 0)
    ):
        print(f"No valid Heroicons usage found in analyzed .templ file(s).")

    return final_icons_list
