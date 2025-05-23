# templ_heroicons_generator/core/downloader.py

import os
import sys
import json
import requests
from hashlib import md5
from typing import List, Dict, Tuple, TYPE_CHECKING

from . import icons as core_icons
from . import config

if TYPE_CHECKING:
    from .icons import Icon


def get_cache_path(url: str, cache_dir: str) -> str:
    """
    Generates a cache file path for a given URL within the specified cache directory.

    The path is based on an MD5 hash of the URL to ensure uniqueness and
    consistent naming.

    Args:
        url: The URL of the resource to be cached.
        cache_dir: The directory where cache files are stored.

    Returns:
        The absolute path to the cache file.
    """
    cache_key = md5(url.encode("utf-8")).hexdigest()
    return os.path.join(cache_dir, f"{cache_key}.svg")


def fetch_heroicons_list(
    verbose: bool = False, silent: bool = False
) -> Dict[str, List[str]]:
    """
    Fetches the list of available Heroicons from the official GitHub repository API.

    It retrieves icon names for both 'outline' and 'solid' styles.
    Uses GITHUB_TOKEN environment variable for authenticated requests if available.

    Args:
        verbose: If True (and silent is False), prints detailed logs.
        silent: If True, suppresses all informational output.

    Returns:
        A dictionary where keys are 'outline' and 'solid', and values are lists
        of icon filenames (without .svg extension). Returns an empty dictionary
        on failure to allow the main process to continue without validation.
    """
    icons_dict: Dict[str, List[str]] = {"outline": [], "solid": []}
    try:
        headers = {"Accept": "application/vnd.github.v3+json"}
        token = os.environ.get("GITHUB_TOKEN")
        if token:
            headers["Authorization"] = f"token {token}"
            if verbose:  # Implies not silent
                print("  Using GITHUB_TOKEN for GitHub API requests.")

        for style in icons_dict.keys():
            style_url = f"{config.HEROICONS_LIST_URL}/{style}"
            if verbose:  # Implies not silent
                print(f"  Fetching icon list for style '{style}' from {style_url}...")
            response = requests.get(
                style_url, headers=headers, timeout=config.REQUEST_TIMEOUT
            )
            response.raise_for_status()
            files_data = response.json()

            if not isinstance(files_data, list):
                if verbose:  # Implies not silent
                    print(
                        f"  Warning: Unexpected API response format for {style} icons. Expected list, got {type(files_data)}.",
                        file=sys.stderr,
                    )
                continue

            icons_dict[style] = [
                item["name"].replace(".svg", "")
                for item in files_data
                if isinstance(item, dict)
                and item.get("type") == "file"
                and item.get("name", "").endswith(".svg")
            ]
            if verbose:  # Implies not silent
                print(f"  Fetched {len(icons_dict[style])} icons for style '{style}'.")

        if (
            not icons_dict["outline"] and not icons_dict["solid"] and verbose
        ):  # Implies not silent
            print(
                "  Warning: Fetched empty icon lists for both styles. Validation might be incomplete.",
                file=sys.stderr,
            )
        return icons_dict

    except requests.exceptions.Timeout:
        # Print warning to stderr if verbose, otherwise it's a silent failure for the list.
        if verbose:  # Implies not silent
            print(
                f"  Warning: Timeout fetching Heroicons list. Skipping remote validation.",
                file=sys.stderr,
            )
    except requests.exceptions.RequestException as e:
        if verbose:  # Implies not silent
            print(
                f"  Warning: Failed to fetch Heroicons list: {e}. Skipping remote validation.",
                file=sys.stderr,
            )
    except json.JSONDecodeError as e:
        if verbose:  # Implies not silent
            print(
                f"  Warning: Failed to parse API response for Heroicons list: {e}. Skipping remote validation.",
                file=sys.stderr,
            )
    except Exception as e:  # Catch any other errors during list fetching
        if verbose:  # Implies not silent
            print(
                f"  Warning: Unexpected error fetching icon list: {e}. Skipping remote validation.",
                file=sys.stderr,
            )
    return {}


def download_svgs(
    icons_to_process: List["Icon"], verbose: bool, silent: bool, cache_dir: str
) -> Tuple[List["Icon"], int]:
    """
    Downloads SVG content for each icon, utilizing a local cache.

    For each icon in `icons_to_process`, this function attempts to read its SVG
    content from a local cache. If not found or if reading fails, it downloads
    the SVG from the official Heroicons repository and caches it. The SVG content
    is then parsed to extract graphical elements, which are stored in the
    icon object.

    Args:
        icons_to_process: A list of `Icon` objects that need their SVG data fetched.
        verbose: If True (and silent is False), prints detailed logs.
        silent: If True, suppresses all informational output except critical errors and progress bar.
        cache_dir: The directory to use for caching downloaded SVG files.

    Returns:
        A tuple containing:
        - A list of `Icon` objects that were successfully processed and have their
          `.elements` attribute populated.
        - An integer count of errors encountered during the download or parsing process.
    """
    if not icons_to_process:
        return [], 0

    abs_cache_dir = os.path.abspath(cache_dir)
    if verbose:  # Implies not silent
        print(f"  Using cache directory: {abs_cache_dir}")

    processed_icons_with_data: List["Icon"] = []
    error_count = 0
    total_icons = len(icons_to_process)
    session = requests.Session()

    try:
        os.makedirs(abs_cache_dir, exist_ok=True)
    except OSError as e:
        # This error is critical enough to inform the user always (to stderr)
        print(
            f"  Error: Could not create cache directory '{abs_cache_dir}': {e}. Caching disabled for this run.",
            file=sys.stderr,
        )
        # If cache dir cannot be created, we might proceed without caching, or fail.
        # For now, we print error and continue; SVGs won't be cached.

    status_bar_width = 40
    last_print_len = 0

    def _print_progress(index: int, current_icon_name: str):
        nonlocal last_print_len
        if silent:
            return  # No progress bar in silent mode

        progress = (index + 1) / total_icons
        filled_width = int(status_bar_width * progress)
        bar = "#" * filled_width + "-" * (status_bar_width - filled_width)
        # Ensure current_icon_name is not too long for display
        display_icon_name = (
            (current_icon_name[:32] + "...")
            if len(current_icon_name) > 35
            else current_icon_name
        )
        line = f"    [{bar}] {index+1}/{total_icons} ({int(progress*100):>3}%) {display_icon_name:<35}"

        # Clear previous line content
        clear_str = "\r" + " " * last_print_len + "\r"
        print(clear_str, end="")

        print(line, end="")
        last_print_len = len(line)
        sys.stdout.flush()

    def _print_message_clean(message: str, is_error: bool = False):
        nonlocal last_print_len
        if silent and not is_error:
            return  # Only print errors in silent mode

        # Clear any existing progress bar line
        if last_print_len > 0:
            print("\r" + " " * last_print_len + "\r", end="")
            last_print_len = 0  # Reset as we are printing a full new line

        print(message, file=sys.stderr if is_error else sys.stdout)
        sys.stdout.flush()  # Ensure it's printed immediately

    for i, icon_obj in enumerate(icons_to_process):
        if not verbose:  # If not verbose, print progress (unless silent)
            _print_progress(i, icon_obj.component_name)

        url = f"{config.HEROICONS_BASE_URL}/{icon_obj.style}/{icon_obj.file_name}.svg"
        current_cache_path = get_cache_path(url, abs_cache_dir)

        if verbose:  # Implies not silent
            print(
                f"    ({i+1}/{total_icons}) Processing {icon_obj.component_name} ({icon_obj.style}/{icon_obj.file_name}.svg)..."
            )
            print(f"      URL: {url}")
            print(f"      Cache path: {os.path.relpath(current_cache_path)}")

        svg_content: str | None = None

        if os.path.exists(current_cache_path):
            if verbose:  # Implies not silent
                print(
                    f"      Cache hit. Reading from: {os.path.relpath(current_cache_path)}"
                )
            try:
                with open(current_cache_path, "r", encoding="utf-8") as f:
                    svg_content = f.read()
            except Exception as e:
                msg = f"    Warning: Error reading cached SVG {os.path.relpath(current_cache_path)}: {e}. Retrying download."
                # This is a warning, print if verbose or if not silent (to stderr)
                if verbose:
                    print(msg, file=sys.stderr)
                elif not silent:
                    _print_message_clean(msg, is_error=True)
        elif verbose:  # Implies not silent (cache miss message)
            print(f"      Cache miss. Downloading...")

        if svg_content is None:
            try:
                response = session.get(url, timeout=config.REQUEST_TIMEOUT)
                response.raise_for_status()
                svg_content = response.text

                try:
                    # Attempt to cache even if os.makedirs failed earlier, might be permissions issue for that specific dir
                    os.makedirs(abs_cache_dir, exist_ok=True)
                    with open(current_cache_path, "w", encoding="utf-8") as f:
                        f.write(svg_content)
                    if verbose:  # Implies not silent
                        print(
                            f"      Downloaded and cached: {os.path.relpath(current_cache_path)}"
                        )
                except Exception as e:
                    # Cache write failure is a warning, not a critical error for the icon itself
                    if verbose:  # Implies not silent
                        print(
                            f"    Warning: Downloaded '{icon_obj.component_name}' but failed to cache to {os.path.relpath(current_cache_path)}: {e}",
                            file=sys.stderr,
                        )
                    # No _print_message_clean here for cache write failure if not verbose, to keep output minimal

            except requests.exceptions.RequestException as e:
                status_code_str = "N/A"
                if hasattr(e, "response") and e.response is not None:
                    status_code_str = str(e.response.status_code)
                error_msg = f"    Error: Failed to download {icon_obj.component_name} (HTTP {status_code_str}): {url}"
                # This is an error, print if verbose OR if not silent (always to stderr)
                if verbose:
                    print(error_msg, file=sys.stderr)
                else:
                    _print_message_clean(
                        error_msg, is_error=True
                    )  # Not silent implies this prints
                error_count += 1
                continue
            except Exception as e:  # Other unexpected download errors
                error_msg = f"    Unexpected error during download of {icon_obj.component_name}: {e}"
                if verbose:
                    print(error_msg, file=sys.stderr)
                else:
                    _print_message_clean(error_msg, is_error=True)
                error_count += 1
                continue

        if svg_content:
            if verbose:
                print(f"      Extracting SVG elements...")  # Implies not silent
            icon_obj.elements = core_icons.extract_svg_elements(svg_content)
            if icon_obj.elements:
                processed_icons_with_data.append(icon_obj)
                if verbose:
                    print(
                        f"      Successfully processed {len(icon_obj.elements)} element(s)."
                    )  # Implies not silent
            else:
                msg = f"    Warning: No graphical SVG elements extracted for {icon_obj.component_name} from {url}."
                if verbose:
                    print(msg, file=sys.stderr)  # Implies not silent
                elif not silent:
                    _print_message_clean(msg, is_error=True)
                error_count += 1
        else:
            error_msg = f"    Error: No SVG content for {icon_obj.component_name} after download/cache attempt."
            if verbose:
                print(error_msg, file=sys.stderr)  # Implies not silent
            else:
                _print_message_clean(error_msg, is_error=True)
            error_count += 1

    if (
        not verbose and not silent and total_icons > 0 and last_print_len > 0
    ):  # Clear progress bar if it was shown
        print("\r" + " " * last_print_len + "\r", end="")
        sys.stdout.flush()

    return processed_icons_with_data, error_count
