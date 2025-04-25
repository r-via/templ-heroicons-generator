#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Generates a heroicons.templ file for a Go Templ project, optimized for production.

Scans specified directories for .templ files, identifies Heroicons usage
(e.g., @heroicons.Outline_bars_3), downloads and caches the corresponding SVG icons
from the official repository, and creates a Go package file (heroicons.templ)
containing Templ components with direct SVG elements. Supports all SVG elements
(path, circle, rect, g, etc.) and includes caching (customizable location),
dry-run mode, and customizable default classes. Generates output with { attrs... }
and fixed class attribute. Avoids writing the output file if the content hasn't changed.
Uses importlib.metadata for dependency checking (Python 3.8+).
"""

import sys
import os
import subprocess
# --- Use the modern importlib.metadata ---
import importlib.metadata
# Required for the exception type
from importlib.metadata import PackageNotFoundError


# --- Dependencies Management ---
REQUIRED_PACKAGES = [
    'requests',
    'jinja2'
]

def check_and_install_dependencies():
    """Check for required packages using importlib.metadata and install them if missing."""
    missing_packages = []
    print("Checking dependencies...") # Add some feedback
    for package in REQUIRED_PACKAGES:
        try:
            # Check for package existence using importlib.metadata
            version = importlib.metadata.version(package)
            # Optional: print installed version if verbose
            # if args.verbose: print(f"  - Found {package} version {version}")
        except PackageNotFoundError:
            print(f"  - Dependency '{package}' not found.")
            missing_packages.append(package)
        except Exception as e: # Catch unexpected errors during version check
             print(f"Warning: Could not check version for package '{package}': {e}", file=sys.stderr)
             # Decide if this should prevent proceeding or just warn

    if missing_packages:
        print(f"Attempting to install missing dependencies: {', '.join(missing_packages)}")
        try:
            # Ensure pip is available and use it to install
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', '--disable-pip-version-check', '--quiet'] + missing_packages)
            print("Dependencies installed successfully.")
            # Re-check after installation attempt (optional but good practice)
            print("Re-verifying installation...")
            final_missing = []
            for pkg in missing_packages:
                try:
                    importlib.metadata.version(pkg)
                    print(f"  - Successfully installed/verified '{pkg}'.")
                except PackageNotFoundError:
                    print(f"ERROR: Failed to find '{pkg}' even after installation attempt.", file=sys.stderr)
                    final_missing.append(pkg)

            if final_missing:
                 print("\nFailed to install the following required packages:", file=sys.stderr)
                 for pkg in final_missing:
                     print(f"  - {pkg}", file=sys.stderr)
                 print("\nPlease install them manually (e.g., 'pip install <package_name>') and rerun the script.", file=sys.stderr)
                 sys.exit(1)

        except subprocess.CalledProcessError as e:
            print(f"\nError during 'pip install': {e}", file=sys.stderr)
            print("Failed to install dependencies automatically.", file=sys.stderr)
            print("Please install the following packages manually:")
            for package in missing_packages:
                print(f"  - {package}")
            sys.exit(1)
        except FileNotFoundError: # Handle case where 'pip' command isn't found via sys.executable -m pip
             print("\nError: 'pip' command not found or accessible.", file=sys.stderr)
             print("Please ensure pip is installed and accessible in your Python environment.", file=sys.stderr)
             print("You may need to install the following packages manually:")
             for package in missing_packages:
                 print(f"  - {package}")
             sys.exit(1)
        except Exception as e: # Catch other potential errors during pip call
             print(f"An unexpected error occurred during dependency installation: {e}", file=sys.stderr)
             sys.exit(1)
    else:
        print("All dependencies are satisfied.")


# Install dependencies first, before importing them
# We call this function before the main imports that depend on these packages
# Note: If this script itself has args, they aren't parsed yet. Consider if verbose needs early parsing.
check_and_install_dependencies()


# Now import the rest after ensuring dependencies are installed
# (These imports will now succeed if check_and_install_dependencies worked)
import argparse
import re
import json
from typing import List, Dict, Optional, Tuple
import requests
import xml.etree.ElementTree as ET
from jinja2 import Environment
from pathlib import Path
from hashlib import md5

# --- Configuration ---
HEROICONS_VERSION = "master"
HEROICONS_BASE_URL = f"https://raw.githubusercontent.com/tailwindlabs/heroicons/{HEROICONS_VERSION}/optimized/24"
HEROICONS_LIST_URL = f"https://api.github.com/repos/tailwindlabs/heroicons/contents/optimized/24"
REQUEST_TIMEOUT = 15
DEFAULT_OUTPUT_DIR = "./components/heroicons"
OUTPUT_FILENAME = "heroicons.templ"
DEFAULT_FALLBACK_PACKAGE = "heroicons"
DEFAULT_CACHE_DIR = "./.heroicons_cache"
DEFAULT_SVG_CLASS = "size-6"

# --- Data Structures ---
class Icon:
    """Represents a Heroicon to be generated."""
    def __init__(self, component_name: str, file_name: str, style: str):
        self.component_name = component_name
        self.file_name = file_name
        self.style = style
        self.elements = []  # List of dicts: {'tag': str, 'attrs': Dict[str, str]}

    def __repr__(self) -> str:
        return f"Icon(component_name='{self.component_name}', style='{self.style}')"

# --- Helper Functions ---
def to_svg_file_name(component_part: str) -> str:
    """Converts a component name part with underscores to SVG file name with hyphens."""
    return component_part.replace('_', '-')

def capitalize_component_name(component_name: str) -> str:
    """Capitalizes the first letter of the component name for export."""
    if not component_name:
        return ""
    parts = component_name.split('_')
    capitalized_parts = [parts[0].capitalize()] + parts[1:]
    return '_'.join(capitalized_parts)

def extract_icon_details(component_name: str) -> Optional[Tuple[str, str, str]]:
    """Extracts file name and style from component name (e.g., Outline_bars_3 -> (bars-3, outline))."""
    original_parts = component_name.split('_', 1)
    if len(original_parts) != 2:
        return None
    style_part, component_part = original_parts
    lower_style = style_part.lower()

    if lower_style not in ["outline", "solid"]:
        return None
    if not component_part:
        return None

    file_name = to_svg_file_name(component_part)
    capitalized_component_name = capitalize_component_name(component_name)
    return file_name, lower_style, capitalized_component_name

def extract_svg_elements(svg_content: str) -> List[Dict[str, any]]:
    """
    Extracts all relevant SVG elements (path, circle, rect, g, etc.) from SVG content.
    Returns a list of dictionaries with tag name and attributes.
    """
    try:
        svg_content = re.sub(r'<\?xml[^>]*\?>', '', svg_content).strip()
        svg_content = re.sub(r'<!--.*?-->', '', svg_content, flags=re.DOTALL).strip()
        # Remove namespaces for simpler parsing if they cause issues, but usually ET handles them.
        # svg_content = re.sub(r' xmlns="[^"]+"', '', svg_content, count=1)
        root = ET.fromstring(svg_content)
        elements = []

        def process_element(elem):
            # Strip namespace prefix if present {http://www.w3.org/2000/svg}tag -> tag
            tag = elem.tag.split('}')[-1]
            if tag in {'path', 'circle', 'rect', 'ellipse', 'line', 'polyline', 'polygon', 'g'}:
                # Copy attributes, excluding namespace definitions if any slip through somehow
                attrs = {k: v for k, v in elem.attrib.items() if 'xmlns' not in k}

                children_elements = []
                for child in elem:
                    child_data = process_element(child)
                    if child_data:
                       # For <g>, process children and collect their elements
                       children_elements.extend(child_data)

                if tag == 'g':
                    # Basic handling: If <g> has attributes (like transforms), they are currently lost.
                    # For Heroicons this is usually okay as they are simple.
                    # A more complex parser would need to handle group attributes.
                    # We directly append the children's graphical elements.
                    elements.extend(children_elements)
                else:
                    # Append the graphical element itself
                    elements.append({'tag': tag, 'attrs': attrs})

                # Return processed children elements (mainly relevant for 'g')
                return children_elements
            return [] # Return empty list for non-graphical/unsupported elements

        # Process direct children of the root <svg> element
        for child in root:
            process_element(child) # Populates the 'elements' list directly

        return elements
    except ET.ParseError as e:
        print(f"\nWarning: Failed to parse SVG content: {e}", file=sys.stderr)
        # Consider logging the problematic svg_content snippet if verbose
        return []
    except Exception as e:
        print(f"\nWarning: Unexpected error during SVG element extraction: {e}", file=sys.stderr)
        return []


def is_valid_go_package_name(name: str) -> bool:
    """Checks if a string is a valid Go package name."""
    if not name:
        return False
    go_keywords = {
        "break", "default", "func", "interface", "select", "case", "defer", "go",
        "map", "struct", "chan", "else", "goto", "package", "switch", "const",
        "fallthrough", "if", "range", "type", "continue", "for", "import", "return", "var"
    }
    return (re.match(r'^[a-z][a-z0-9_]*$', name) is not None and
            name not in go_keywords and name != "_")

def get_cache_path(url: str, cache_dir: str) -> str:
    """Generates a cache file path based on the URL's MD5 hash within the specified cache directory."""
    cache_key = md5(url.encode('utf-8')).hexdigest()
    return os.path.join(cache_dir, f"{cache_key}.svg")

def fetch_heroicons_list(verbose: bool) -> Dict[str, List[str]]:
    """Fetches the list of available Heroicons from the repository."""
    icons: Dict[str, List[str]] = {'outline': [], 'solid': []}
    try:
        headers = {'Accept': 'application/vnd.github.v3+json'}
        token = os.environ.get('GITHUB_TOKEN')
        if token:
            headers['Authorization'] = f'token {token}'
            if verbose:
                 print("Using GITHUB_TOKEN for API requests.")

        for style in icons.keys():
            style_url = f"{HEROICONS_LIST_URL}/{style}"
            if verbose:
                print(f"Fetching icon list for style '{style}' from {style_url}...")
            response = requests.get(style_url, headers=headers, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
            files = response.json()
            if not isinstance(files, list):
                 print(f"Warning: Unexpected response format for {style} icons list. Expected a list, got {type(files)}.", file=sys.stderr)
                 continue

            icons[style] = [f['name'].replace('.svg', '')
                            for f in files
                            if isinstance(f, dict) and f.get('type') == 'file' and f.get('name', '').endswith('.svg')]
            if verbose:
                print(f"Fetched {len(icons[style])} icons for style '{style}'.")

        if not icons['outline'] and not icons['solid']:
             print("Warning: Fetched empty lists for both outline and solid icons. Validation might be incomplete.", file=sys.stderr)
        return icons

    except requests.exceptions.Timeout:
        print(f"Warning: Timeout while fetching Heroicons list from GitHub API. Skipping validation.", file=sys.stderr)
        return {}
    except requests.exceptions.RequestException as e:
        print(f"Warning: Failed to fetch Heroicons list: {e}. Skipping validation.", file=sys.stderr)
        return {}
    except json.JSONDecodeError as e:
        print(f"Warning: Failed to parse JSON response from GitHub API: {e}. Skipping validation.", file=sys.stderr)
        return {}
    except Exception as e:
        print(f"Warning: An unexpected error occurred while fetching the icon list: {e}. Skipping validation.", file=sys.stderr)
        return {}

# --- Core Logic Functions ---
def parse_args() -> argparse.Namespace:
    """Parses command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Generate a heroicons.templ file from used icons, optimized for production.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument(
        "--input-dir", "-i", default=".",
        help="Root directory of the project containing .templ files to scan."
    )
    parser.add_argument(
        "--output-dir", "-o", default=DEFAULT_OUTPUT_DIR,
        help=f"Output directory for {OUTPUT_FILENAME}. The Go package name is derived from this directory's base name."
    )
    parser.add_argument(
        "--force", "-f", action="store_true",
        help="Overwrite the output file if it exists, even if content is identical."
    )
    parser.add_argument(
        "--exclude-output", type=lambda x: str(x).lower() not in ['false', '0', 'no'],
        default=True,
        help="Exclude .templ files within the --output-dir from scanning (true/false)."
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true",
        help="Enable verbose output during scanning and downloading."
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Preview the generated output without writing to disk."
    )
    parser.add_argument(
        "--default-class", default=DEFAULT_SVG_CLASS,
        help="Default CSS class attribute value for SVG elements."
    )
    parser.add_argument(
        "--cache-dir", default=DEFAULT_CACHE_DIR,
        help="Directory to store cached SVG files."
    )
    return parser.parse_args()

def find_used_icons(input_dir: str, output_dir: str, exclude_output: bool, verbose: bool, valid_icons: Dict[str, List[str]]) -> List[Icon]:
    """Scans .templ files recursively to find used Heroicons."""
    if not os.path.isdir(input_dir):
        print(f"Error: Input directory '{input_dir}' not found or is not a directory.", file=sys.stderr)
        sys.exit(1)

    abs_input_dir = os.path.abspath(input_dir)
    abs_output_dir = os.path.abspath(os.path.join(input_dir, output_dir)) if not os.path.isabs(output_dir) else os.path.abspath(output_dir)
    icon_pattern = re.compile(r'@heroicons\.([A-Z][a-zA-Z0-9]*_[a-zA-Z0-9_]+)\b')
    icon_dict: Dict[str, Icon] = {}
    templ_files_found = []

    print(f"Scanning for .templ files in '{abs_input_dir}'...")
    if verbose:
        print(f"  Excluding scans within: '{abs_output_dir}' (if applicable and --exclude-output is true)")

    for root, _, files in os.walk(abs_input_dir):
        abs_root = os.path.abspath(root)
        is_in_output_dir = abs_root == abs_output_dir or abs_root.startswith(abs_output_dir + os.sep)
        if exclude_output and is_in_output_dir:
            if verbose:
                print(f"  Skipping directory: {os.path.relpath(abs_root)} (within output directory)")
            continue
        for file in files:
            if file.endswith(".templ"):
                templ_files_found.append(os.path.abspath(os.path.join(root, file)))

    if not templ_files_found:
        print("No .templ files found in the specified input directory (excluding output directory if applicable).")
        return []

    print(f"Analyzing {len(templ_files_found)} .templ file(s)...")
    files_with_errors = 0
    processed_icons_count = 0
    unique_icons_found = set()

    for file_path in templ_files_found:
        relative_file_path = os.path.relpath(file_path)
        if verbose:
            print(f"  - Analyzing: {relative_file_path}")
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
                matches = icon_pattern.findall(content)
                if not matches and verbose > 1: # Higher verbosity for files with no matches
                     print(f"    No heroicon patterns found in {relative_file_path}.")
                for component_name in matches:
                    processed_icons_count += 1
                    unique_icons_found.add(component_name)
                    if component_name not in icon_dict:
                        details = extract_icon_details(component_name)
                        if details:
                            file_name, style, capitalized_component_name = details
                            # Perform validation only if valid_icons list is usable
                            is_known_icon = True
                            if valid_icons and style in valid_icons:
                                if file_name not in valid_icons[style]:
                                    is_known_icon = False
                                    print(f"    Warning: Icon '@heroicons.{component_name}' found in {relative_file_path}, but '{file_name}.svg' is not a known {style} icon (based on fetched list). Skipping.", file=sys.stderr)
                            elif valid_icons and style not in valid_icons:
                                # This case shouldn't happen if fetch worked, but good to handle
                                print(f"    Warning: Style '{style}' not found in fetched icon lists for '@heroicons.{component_name}' in {relative_file_path}. Skipping.", file=sys.stderr)
                                is_known_icon = False

                            if is_known_icon:
                                icon_dict[component_name] = Icon(capitalized_component_name, file_name, style)
                                if verbose:
                                    print(f"    Found valid icon usage: {capitalized_component_name} ({style}, {file_name}.svg)")
                        elif verbose:
                             print(f"    Warning: Could not parse icon details for matched '@heroicons.{component_name}' in {relative_file_path}. Check format (e.g., Style_icon_name).")
        except FileNotFoundError:
             print(f"  Error: File not found during analysis {relative_file_path}. It might have been moved or deleted.", file=sys.stderr)
             files_with_errors += 1
        except Exception as e:
            print(f"  Error reading or processing file {relative_file_path}: {e}", file=sys.stderr)
            files_with_errors += 1

    if files_with_errors > 0:
        print(f"Warning: Encountered errors while reading {files_with_errors} file(s). Results might be incomplete.", file=sys.stderr)

    icons = list(icon_dict.values())
    total_unique_references = len(unique_icons_found)
    valid_unique_icons = len(icons)

    if icons:
        icons.sort(key=lambda x: x.component_name)
        print(f"Found {valid_unique_icons} unique valid Heroicons to generate (out of {total_unique_references} unique references found across {processed_icons_count} total usages):")
        if verbose:
            for icon in icons:
                print(f"  - {icon.component_name} ({icon.style} -> {icon.file_name}.svg)")
        else:
            names = [icon.component_name for icon in icons[:10]]
            print(f"  [{', '.join(names)}{'...' if len(icons) > 10 else ''}]")
    else:
        # Distinguish between no files found vs files found but no icons
        if templ_files_found:
             print(f"No valid Heroicons usage matching the format '@heroicons.Style_icon_name' found in the scanned files ({total_unique_references} unique patterns seen, {processed_icons_count} total).")
        # else: message handled earlier


    # Report skipped icons if any unique references were found but didn't make it to the final list
    skipped_count = total_unique_references - valid_unique_icons
    if skipped_count > 0:
         print(f"Note: {skipped_count} unique icon reference(s) were skipped due to parsing errors or failed validation (see warnings above).")


    return icons

def download_svgs(icons: List[Icon], verbose: bool, cache_dir: str) -> Tuple[List[Icon], int]:
    """
    Downloads SVG content for each icon, using cache if available.
    Uses the specified cache_dir and displays a progress bar in non-verbose mode,
    ensuring updates even with cache hits.
    """
    if not icons:
        return [], 0

    print(f"Processing SVGs for {len(icons)} icon(s)...")
    abs_cache_dir = os.path.abspath(cache_dir)
    if verbose: # Only print cache dir if verbose
        print(f"Using cache directory: {abs_cache_dir}")
    processed_icons = []
    errors = 0
    total = len(icons)
    session = requests.Session()

    try:
        os.makedirs(abs_cache_dir, exist_ok=True)
    except OSError as e:
        # This message will print above the progress bar, which is acceptable
        print(f"Error: Could not create cache directory '{abs_cache_dir}': {e}", file=sys.stderr)
        print("Caching will be disabled for this run.", file=sys.stderr)

    status_bar_width = 40
    last_print_len = 0 # Track length to clear line

    # --- Internal helper to print progress bar ---
    def print_progress(index, status_message=""):
        nonlocal last_print_len
        progress = (index + 1) / total
        filled_width = int(status_bar_width * progress)
        bar = '#' * filled_width + '-' * (status_bar_width - filled_width)
        # Simplified status message for non-verbose mode for clarity
        line = f"  [{bar}] {index+1}/{total} ({int(progress*100):>3}%) {icon.component_name:<35}" # Show icon name being processed
        clear_line = " " * max(0, last_print_len - len(line))
        print(f"\r{line}{clear_line}", end="")
        last_print_len = len(line)
        sys.stdout.flush() # Force update

    # --- Internal helper to print messages cleanly (same as before) ---
    def print_message_clean(message, is_error=False):
        nonlocal last_print_len
        print("\r" + " " * last_print_len + "\r", end="")
        print(message, file=sys.stderr if is_error else sys.stdout)
        last_print_len = 0
        # Do not redraw progress bar here, next iteration will handle it

    # --- Main Loop ---
    for i, icon in enumerate(icons):
        # --- Update progress bar at the START of each iteration in non-verbose mode ---
        # This ensures *something* is always displayed for each icon.
        if not verbose:
            print_progress(i) # Pass index, message is generated inside using current icon

        url = f"{HEROICONS_BASE_URL}/{icon.style}/{icon.file_name}.svg"
        cache_path = get_cache_path(url, cache_dir)

        if verbose: # Verbose logging block
            print(f"  ({i+1}/{total}) Processing {icon.component_name} ({icon.style}/{icon.file_name}.svg)...")
            print(f"    URL: {url}")
            print(f"    Cache path: {os.path.relpath(cache_path)}")

        svg_content = None
        cache_hit = False
        action_taken = "Processing" # Default status

        # Check cache first
        if os.path.exists(cache_path):
            action_taken = "Using cache"
            if verbose:
                print(f"    Cache hit. Reading from: {os.path.relpath(cache_path)}")
            try:
                with open(cache_path, 'r', encoding='utf-8') as f:
                    svg_content = f.read()
                cache_hit = True
            except Exception as e:
                msg = f"  Warning: Error reading cached SVG {os.path.relpath(cache_path)}: {e}. Attempting redownload."
                if verbose: print(msg, file=sys.stderr)
                else: print_message_clean(msg, is_error=True)
                svg_content = None
                cache_hit = False # Treat as miss
                action_taken = "Cache read failed"
        elif verbose:
             print(f"    Cache miss. Downloading...")
             action_taken = "Downloading"


        # Download if needed
        if svg_content is None:
            # Only update status if we are actually downloading
            if not verbose and not cache_hit: # Don't overwrite if cache read failed
                 pass # print_progress(i) # Already updated at start
            try:
                response = session.get(url, timeout=REQUEST_TIMEOUT)
                response.raise_for_status()
                svg_content = response.text
                action_taken = "Downloaded" # Update status after successful download

                # Cache the downloaded SVG
                try:
                    os.makedirs(os.path.dirname(cache_path), exist_ok=True)
                    with open(cache_path, 'w', encoding='utf-8') as f:
                        f.write(svg_content)
                    if verbose:
                        print(f"    Downloaded successfully. Cached to: {os.path.relpath(cache_path)}")
                except Exception as e:
                    msg = f"  Warning: Downloaded '{icon.component_name}' but failed to write cache to {os.path.relpath(cache_path)}: {e}"
                    if verbose: print(msg, file=sys.stderr)
                    # Don't use print_message_clean here as it's just a non-fatal warning post-download
                    # else: print_message_clean(msg, is_error=True)

            except requests.exceptions.RequestException as e:
                 error_msg = ""
                 if isinstance(e, requests.exceptions.Timeout): error_msg = f"  Error: Timeout downloading {icon.component_name}"
                 elif isinstance(e, requests.exceptions.HTTPError): error_msg = f"  Error: HTTP {e.response.status_code} downloading {icon.component_name}"
                 else: error_msg = f"  Error: Network issue downloading {icon.component_name}: {e}"

                 if verbose: print(error_msg, file=sys.stderr)
                 else: print_message_clean(error_msg, is_error=True)
                 errors += 1
                 continue # Skip
            except Exception as e:
                 error_msg = f"  Unexpected error during download for {icon.component_name}: {e}"
                 if verbose: print(error_msg, file=sys.stderr)
                 else: print_message_clean(error_msg, is_error=True)
                 errors += 1
                 continue # Skip

        # Process SVG content if obtained
        if svg_content:
            action_taken = "Parsing"
            if verbose: print(f"    Extracting SVG elements...")

            # No need to update progress bar again here in non-verbose, already shown at start.
            # if not verbose: print_progress(i)

            icon.elements = extract_svg_elements(svg_content)
            if icon.elements:
                processed_icons.append(icon)
                action_taken = "Processed"
                if verbose: print(f"    Successfully processed {len(icon.elements)} element(s).")
            else:
                 msg = f"  Warning: No graphical SVG elements extracted for {icon.component_name}."
                 if verbose: print(msg, file=sys.stderr)
                 else: print_message_clean(msg, is_error=True)
                 errors += 1
                 action_taken = "Parse failed"
                 continue # Skip adding this icon
        else:
             error_msg = f"  Error: Failed to obtain SVG content for {icon.component_name}."
             if verbose: print(error_msg, file=sys.stderr)
             else: print_message_clean(error_msg, is_error=True)
             errors += 1
             action_taken = "Content failed"
             continue

        # --- Optional: Update progress bar one last time with final status for the icon ---
        # This might make it look slightly better but could also be too fast. Test if needed.
        # if not verbose:
        #    print_progress(i) # Update with the final state (name implicitly shown)


    # Final cleanup
    if not verbose:
        print("\r" + " " * last_print_len + "\r", end="")
        sys.stdout.flush()

    # Final Summary
    if errors > 0:
        print(f"SVG processing finished with {errors} error(s). See messages above.", file=sys.stderr)
    else:
        print("SVG processing complete.")

    return processed_icons, errors

def generate_heroicons_package(output_dir: str, icons: List[Icon], force: bool, verbose: bool, dry_run: bool, default_class: str) -> Optional[str]:
    """
    Generates the heroicons.templ file or returns content for dry-run.
    Avoids writing the file if the content hasn't changed, unless --force is used.
    """
    # --- Determine Package Name ---
    normalized_output_dir = os.path.normpath(output_dir)
    derived_package_name = os.path.basename(normalized_output_dir)
    if not derived_package_name or derived_package_name in ('.', '..'):
        derived_package_name = os.path.basename(os.path.abspath(output_dir))

    if not is_valid_go_package_name(derived_package_name):
        print(f"Warning: Derived package name '{derived_package_name}' from '{output_dir}' is invalid. Using fallback '{DEFAULT_FALLBACK_PACKAGE}'.", file=sys.stderr)
        package_name = DEFAULT_FALLBACK_PACKAGE
    else:
        package_name = derived_package_name
        if verbose:
             print(f"Using Go package name: '{package_name}'")

    # --- Prepare Output Path ---
    output_path = os.path.join(output_dir, OUTPUT_FILENAME)
    abs_output_path = os.path.abspath(output_path)
    output_dirname = os.path.dirname(abs_output_path)
    relative_output_path = os.path.relpath(abs_output_path) # For user messages

    print(f"Generating content for {relative_output_path} with {len(icons)} icon(s) for package '{package_name}'...")

    # --- Render Template ---
    # Use html.escape for attribute values within Jinja template for safety
    import html
    env = Environment(
        trim_blocks=True,
        lstrip_blocks=True,
        keep_trailing_newline=True,
        autoescape=True # Enable autoescaping for HTML context
    )
    # Add html.escape as a filter if needed, though autoescape might handle it.
    # env.filters['escape_attr'] = html.escape # Example if specific escaping needed

    template_str = """\
// Code generated by generate_heroicons.py. DO NOT EDIT.
// Source: {{ HEROICONS_BASE_URL }}
// Version: {{ HEROICONS_VERSION }}
package {{ package_name }}

// Requires: templ v0.2.513 or later
// Web: https://heroicons.com/
{% if not icons %}
// No icons found or processed by the generation script.
{% endif %}
{% for icon in icons %}
// {{ icon.component_name }} renders the '{{ icon.file_name }}' icon ({{ icon.style }} style).
// Source: {{ HEROICONS_BASE_URL }}/{{ icon.style }}/{{ icon.file_name }}.svg
templ {{ icon.component_name }}(attrs templ.Attributes) {
	<svg
		xmlns="http://www.w3.org/2000/svg"
		{# Add newlines and indentation for SVG attributes #}
		{% if icon.style == 'outline' %}
		fill="none"
		viewBox="0 0 24 24"
		stroke-width="1.5"
		stroke="currentColor"
		{% else %}
		fill="currentColor"
		viewBox="0 0 24 24"
		{% endif %}
        { attrs... }
		class="{{ default_class }}"
	>
		{# Ensure newline/indentation before inner elements #}
		{% for element in icon.elements %}
		<{{ element.tag }}
			{# Loop through element attributes, adding newline/indent for each #}
			{% for key, value in element.attrs.items() %}
			{{ key }}="{{ value }}"
			{% endfor %}
		/>
		{% endfor %}
	</svg>
}
{% endfor %}
"""
# Note: Jinja's autoescape should handle attribute value escaping. If issues arise,
# consider using `value | e` explicitly or the custom `escape_attr` filter.
# The current template relies on autoescape doing the right thing for `value`.

    try:
        template = env.from_string(template_str)
        rendered_content = template.render(
            icons=icons,
            HEROICONS_BASE_URL=HEROICONS_BASE_URL,
            HEROICONS_VERSION=HEROICONS_VERSION,
            package_name=package_name,
            default_class=default_class
        ).strip() + "\n" # Ensure single trailing newline
    except Exception as e:
        print(f"Error rendering template: {e}", file=sys.stderr)
        # Optionally print traceback if verbose
        # if verbose: import traceback; traceback.print_exc()
        sys.exit(1)

    # --- Handle Dry Run ---
    if dry_run:
        print(f"\n--- Dry Run: Would generate {relative_output_path} ---")
        print(rendered_content.strip()) # Print content without extra newline for dry run display
        print("--- End Dry Run ---")
        return rendered_content # Return content for potential testing

    # --- Check for Changes and Write File ---
    try:
        os.makedirs(output_dirname, exist_ok=True) # Ensure output directory exists
    except OSError as e:
         print(f"Error: Could not create output directory '{output_dirname}': {e}", file=sys.stderr)
         sys.exit(1)


    file_exists = os.path.exists(abs_output_path)
    should_write = True

    if file_exists and not force:
        try:
            with open(abs_output_path, "r", encoding="utf-8") as f:
                existing_content = f.read()
            # Normalize line endings for robust comparison
            normalized_existing = existing_content.replace('\r\n', '\n').strip()
            normalized_rendered = rendered_content.replace('\r\n', '\n').strip()

            if normalized_existing == normalized_rendered:
                print(f"Content of '{relative_output_path}' is up-to-date. No changes needed.")
                should_write = False
            else:
                if verbose:
                    print(f"Content of '{relative_output_path}' differs. Will overwrite.")
                # Add diff output here if desired (requires 'difflib')
                # import difflib
                # diff = difflib.unified_diff(existing_content.splitlines(keepends=True),
                #                             rendered_content.splitlines(keepends=True),
                #                             fromfile='existing', tofile='new')
                # print("--- Diff ---")
                # sys.stdout.writelines(diff)
                # print("--- End Diff ---")

        except Exception as e:
            print(f"Warning: Could not read existing file '{relative_output_path}' for comparison: {e}. Proceeding with overwrite.", file=sys.stderr)
            # Keep should_write = True to attempt overwrite

    elif file_exists and force:
        if verbose:
            print(f"Force flag enabled. Overwriting '{relative_output_path}' regardless of content.")
        should_write = True # Default behavior when forcing

    elif not file_exists:
        if verbose:
            print(f"Output file '{relative_output_path}' does not exist. Will create.")
        should_write = True # Default behavior when file doesn't exist

    if should_write:
        try:
            with open(abs_output_path, "w", encoding="utf-8", newline='\n') as f: # Use newline='\n' for consistent line endings
                f.write(rendered_content)
            action_word = "Created" if not file_exists else "Updated"
            print(f"Successfully {action_word.lower()} {relative_output_path}")
        except IOError as e:
            print(f"Error: Failed writing to '{abs_output_path}': {e}", file=sys.stderr)
            sys.exit(1)
        except Exception as e: # Catch other potential write errors
             print(f"An unexpected error occurred while writing the output file '{abs_output_path}': {e}", file=sys.stderr)
             sys.exit(1)


    return rendered_content # Return the content even if not written


# --- Main Execution ---
if __name__ == "__main__":
    # Parse args early to use for verbose flag if needed during dependency check potentially
    # Although currently verbose logging only happens after parsing.
    args = parse_args()
    exit_code = 0

    try:
        # 1. Fetch valid Heroicons list (important for validation)
        print("Fetching available Heroicons list from GitHub API...")
        valid_icons_list = fetch_heroicons_list(args.verbose)
        if not valid_icons_list:
             print("Warning: Could not fetch or parse the list of available icons. Validation against the official list will be skipped.", file=sys.stderr)
        elif args.verbose:
             print("Icon list fetched successfully.")

        # 2. Find used icons in the project
        icons_to_generate = find_used_icons(
            args.input_dir,
            args.output_dir,
            args.exclude_output,
            args.verbose,
            valid_icons_list # Pass the fetched list for validation
        )

        # Handle case where no icons are found - still might need to update/create empty file
        if not icons_to_generate and not args.dry_run:
             print("No icons found in project files matching the required format.")
             # Proceed to download/generate steps - they will handle the empty list
             # This ensures the output file is correctly generated/updated even if empty


        # 3. Download/Cache SVGs and extract elements
        # Pass the cache directory from args to download_svgs
        valid_icons_data, download_errors = download_svgs(
            icons_to_generate,
            args.verbose,
            args.cache_dir # Use the specified cache directory
        )

        # Exit if critical download errors occurred and no icons could be processed, unless dry-running
        if download_errors > 0 and not valid_icons_data and icons_to_generate and not args.dry_run:
             # Only exit if there were icons to begin with but none succeeded
             print(f"\nError: Failed to process any of the {len(icons_to_generate)} identified icons due to {download_errors} errors. Cannot generate package.", file=sys.stderr)
             sys.exit(1)
        elif download_errors > 0 and icons_to_generate: # Print warning only if there were icons initially
             print(f"\nWarning: Proceeding with {len(valid_icons_data)} successfully processed icons despite {download_errors} errors during SVG fetching/parsing.", file=sys.stderr)


        # 4. Generate the Templ package file (handles writing/dry-run/no-change logic internally)
        generate_heroicons_package(
            args.output_dir,
            valid_icons_data, # Use the list of icons that were successfully processed
            args.force,
            args.verbose,
            args.dry_run,
            args.default_class
        )

    except SystemExit as e:
        # Catch sys.exit calls, ensuring exit code is an integer
        exit_code = e.code if isinstance(e.code, int) else 1
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.", file=sys.stderr)
        exit_code = 130 # Standard exit code for Ctrl+C
    except requests.exceptions.RequestException as e:
         # Catch potential requests errors not handled in specific functions (e.g., if used elsewhere)
         print(f"\nNetwork Error: An unexpected network error occurred: {e}", file=sys.stderr)
         exit_code = 1
    except Exception as e:
        # Generic catch-all for truly unexpected errors
        import traceback
        print(f"\n--- Unexpected Error ---", file=sys.stderr)
        print(f"An unhandled error occurred: {e}", file=sys.stderr)
        print("\n--- Traceback ---", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        print("--- End Traceback ---", file=sys.stderr)
        exit_code = 1
    finally:
         # Ensure script exits with the determined code
         if exit_code == 0:
             print("Script finished successfully.")
         else:
             print(f"Script finished with errors (exit code {exit_code}).")
         sys.exit(exit_code)
