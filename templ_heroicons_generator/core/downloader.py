# templ_heroicons_generator/core/downloader.py

import os
import sys
import json
import requests
from hashlib import md5
import time
from typing import List, Dict, Tuple, TYPE_CHECKING

from . import icons as core_icons
from . import config

if TYPE_CHECKING:
    from .icons import Icon

ICON_LIST_CACHE_FILENAME = "heroicons_list_cache.json"
ICON_LIST_CACHE_DURATION_SECONDS = 24 * 60 * 60  # 24 hours


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


def _read_icon_list_from_cache(
    cache_file_path: str, verbose: bool, silent: bool
) -> Dict[str, List[str]] | None:
    """
    Attempts to read the icon list from a cache file if it exists and is recent.

    Args:
        cache_file_path: The path to the icon list cache file.
        verbose: If True (and silent is False), prints detailed logs.
        silent: If True, suppresses all informational output.

    Returns:
        The cached icon list as a dictionary if successful, otherwise None.
    """
    try:
        if os.path.exists(cache_file_path):
            file_mod_time = os.path.getmtime(cache_file_path)
            if (time.time() - file_mod_time) < ICON_LIST_CACHE_DURATION_SECONDS:
                with open(cache_file_path, "r", encoding="utf-8") as f:
                    cached_data = json.load(f)
                if (
                    isinstance(cached_data, dict)
                    and "outline" in cached_data
                    and "solid" in cached_data
                ):
                    if verbose:
                        print(
                            f"  Using cached Heroicons list (less than {ICON_LIST_CACHE_DURATION_SECONDS // 3600}h old from '{os.path.relpath(cache_file_path)}')."
                        )
                    return cached_data
                elif verbose:
                    print(
                        f"  Cached Heroicons list at '{os.path.relpath(cache_file_path)}' has invalid format. Will refresh.",
                        file=sys.stderr,
                    )
            elif verbose:
                print(
                    f"  Cached Heroicons list at '{os.path.relpath(cache_file_path)}' is older than {ICON_LIST_CACHE_DURATION_SECONDS // 3600}h. Will refresh."
                )
        elif verbose:
            print(
                f"  No local cache for Heroicons list found at '{os.path.relpath(cache_file_path)}'. Will fetch."
            )
    except json.JSONDecodeError as e:
        if verbose:
            print(
                f"  Error decoding cached Heroicons list '{os.path.relpath(cache_file_path)}': {e}. Will refresh.",
                file=sys.stderr,
            )
    except OSError as e:
        if verbose:
            print(
                f"  Error accessing cached Heroicons list '{os.path.relpath(cache_file_path)}': {e}. Will refresh.",
                file=sys.stderr,
            )
    except Exception as e:
        if verbose:
            print(
                f"  Unexpected error reading cached Heroicons list '{os.path.relpath(cache_file_path)}': {e}. Will refresh.",
                file=sys.stderr,
            )
    return None


def _write_icon_list_to_cache(
    cache_file_path: str, data: Dict[str, List[str]], verbose: bool, silent: bool
):
    """
    Writes the fetched icon list to a cache file.

    Args:
        cache_file_path: The path to the icon list cache file.
        data: The icon list dictionary to cache.
        verbose: If True (and silent is False), prints detailed logs.
        silent: If True, suppresses all informational output.
    """
    try:
        os.makedirs(os.path.dirname(cache_file_path), exist_ok=True)
        with open(cache_file_path, "w", encoding="utf-8") as f:
            json.dump(data, f)
        if verbose:
            print(
                f"  Heroicons list cached locally to '{os.path.relpath(cache_file_path)}'."
            )
    except OSError as e:
        if verbose:
            print(
                f"  Warning: Failed to write Heroicons list to cache at '{os.path.relpath(cache_file_path)}': {e}",
                file=sys.stderr,
            )
    except Exception as e:
        if verbose:
            print(
                f"  Warning: Unexpected error writing Heroicons list to cache '{os.path.relpath(cache_file_path)}': {e}",
                file=sys.stderr,
            )


def fetch_heroicons_list(
    cache_dir: str, verbose: bool = False, silent: bool = False
) -> Dict[str, List[str]]:
    """
    Fetches the list of available Heroicons from the GitHub API, using a local cache
    if available and recent.

    Args:
        cache_dir: Directory to store and read the cache file for the icon list.
        verbose: If True (and silent is False), prints detailed logs.
        silent: If True, suppresses all informational output.

    Returns:
        A dictionary where keys are 'outline' and 'solid', and values are lists
        of icon filenames (without .svg extension). Returns an empty dictionary
        on failure if cache is also unavailable/invalid.
    """
    abs_cache_dir = os.path.abspath(cache_dir)
    icon_list_cache_file = os.path.join(abs_cache_dir, ICON_LIST_CACHE_FILENAME)

    cached_icons = _read_icon_list_from_cache(icon_list_cache_file, verbose, silent)
    if cached_icons is not None:
        return cached_icons

    if not silent and not verbose:
        print(
            "Fetching available Heroicons list from GitHub API (cache miss or expired)..."
        )
    elif verbose:
        print(
            "  Fetching fresh Heroicons list from GitHub API (cache miss, expired, or invalid)..."
        )

    icons_dict: Dict[str, List[str]] = {"outline": [], "solid": []}
    api_fetch_successful = False
    try:
        headers = {"Accept": "application/vnd.github.v3+json"}
        token = os.environ.get("GITHUB_TOKEN")
        if token:
            headers["Authorization"] = f"token {token}"
            if verbose:
                print("  Using GITHUB_TOKEN for GitHub API requests.")

        for style in icons_dict.keys():
            style_url = f"{config.HEROICONS_LIST_URL}/{style}"
            if verbose:
                print(f"  Fetching icon list for style '{style}' from {style_url}...")
            response = requests.get(
                style_url, headers=headers, timeout=config.REQUEST_TIMEOUT
            )
            response.raise_for_status()
            files_data = response.json()

            if not isinstance(files_data, list):
                if verbose:
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
            if verbose:
                print(f"  Fetched {len(icons_dict[style])} icons for style '{style}'.")

        if icons_dict["outline"] or icons_dict["solid"]:
            api_fetch_successful = True

    except requests.exceptions.Timeout:
        if verbose:
            print(
                f"  Warning: Timeout fetching Heroicons list. Validation might be based on older cache or skipped.",
                file=sys.stderr,
            )
    except requests.exceptions.RequestException as e:
        if verbose:
            print(
                f"  Warning: Failed to fetch Heroicons list: {e}. Validation might be based on older cache or skipped.",
                file=sys.stderr,
            )
    except json.JSONDecodeError as e:
        if verbose:
            print(
                f"  Warning: Failed to parse API response for Heroicons list: {e}. Validation might be based on older cache or skipped.",
                file=sys.stderr,
            )
    except Exception as e:
        if verbose:
            print(
                f"  Warning: Unexpected error fetching icon list: {e}. Validation might be based on older cache or skipped.",
                file=sys.stderr,
            )

    if api_fetch_successful:
        _write_icon_list_to_cache(icon_list_cache_file, icons_dict, verbose, silent)
        return icons_dict
    else:
        if verbose:
            print(
                "  API fetch for Heroicons list failed and no valid recent cache available. Skipping remote validation.",
                file=sys.stderr,
            )
        return {}


def download_svgs(
    icons_to_process: List["Icon"], verbose: bool, silent: bool, cache_dir: str
) -> Tuple[List["Icon"], int]:
    """
    Downloads SVG content for each icon, utilizing a local cache for individual SVGs.

    Args:
        icons_to_process: A list of `Icon` objects that need their SVG data fetched.
        verbose: If True (and silent is False), prints detailed logs.
        silent: If True, suppresses all informational output except critical errors and progress bar.
        cache_dir: The directory to use for caching downloaded individual SVG files.

    Returns:
        A tuple containing:
        - A list of `Icon` objects that were successfully processed and have their
          `.elements` attribute populated.
        - An integer count of errors encountered during the download or parsing process.
    """
    if not icons_to_process:
        return [], 0

    abs_svg_cache_dir = os.path.abspath(cache_dir)
    if verbose:
        print(f"  Using SVG cache directory: {abs_svg_cache_dir}")

    processed_icons_with_data: List["Icon"] = []
    error_count = 0
    total_icons = len(icons_to_process)
    session = requests.Session()

    try:
        os.makedirs(abs_svg_cache_dir, exist_ok=True)
    except OSError as e:
        print(
            f"  Error: Could not create SVG cache directory '{abs_svg_cache_dir}': {e}. SVG Caching disabled for this run.",
            file=sys.stderr,
        )

    status_bar_width = 40
    last_print_len = 0

    def _print_progress(index: int, current_icon_name: str):
        nonlocal last_print_len
        if silent:
            return

        progress = (index + 1) / total_icons
        filled_width = int(status_bar_width * progress)
        bar = "#" * filled_width + "-" * (status_bar_width - filled_width)
        display_icon_name = (
            (current_icon_name[:32] + "...")
            if len(current_icon_name) > 35
            else current_icon_name
        )
        line = f"    [{bar}] {index+1}/{total_icons} ({int(progress*100):>3}%) {display_icon_name:<35}"

        clear_str = "\r" + " " * last_print_len + "\r"
        print(clear_str, end="")

        print(line, end="")
        last_print_len = len(line)
        sys.stdout.flush()

    def _print_message_clean(message: str, is_error: bool = False):
        nonlocal last_print_len
        if silent and not is_error:
            return

        if last_print_len > 0:
            print("\r" + " " * last_print_len + "\r", end="")
            last_print_len = 0

        print(message, file=sys.stderr if is_error else sys.stdout)
        sys.stdout.flush()

    for i, icon_obj in enumerate(icons_to_process):
        if not verbose:
            _print_progress(i, icon_obj.component_name)

        url = f"{config.HEROICONS_BASE_URL}/{icon_obj.style}/{icon_obj.file_name}.svg"
        current_svg_cache_path = get_cache_path(url, abs_svg_cache_dir)

        if verbose:
            print(
                f"    ({i+1}/{total_icons}) Processing {icon_obj.component_name} ({icon_obj.style}/{icon_obj.file_name}.svg)..."
            )
            print(f"      URL: {url}")
            print(f"      SVG Cache path: {os.path.relpath(current_svg_cache_path)}")

        svg_content: str | None = None

        if os.path.exists(current_svg_cache_path):
            if verbose:
                print(
                    f"      SVG Cache hit. Reading from: {os.path.relpath(current_svg_cache_path)}"
                )
            try:
                with open(current_svg_cache_path, "r", encoding="utf-8") as f:
                    svg_content = f.read()
            except Exception as e:
                msg = f"    Warning: Error reading cached SVG {os.path.relpath(current_svg_cache_path)}: {e}. Retrying download."
                if verbose:
                    print(msg, file=sys.stderr)
                elif not silent:
                    _print_message_clean(msg, is_error=True)
        elif verbose:
            print(f"      SVG Cache miss. Downloading...")

        if svg_content is None:
            try:
                response = session.get(url, timeout=config.REQUEST_TIMEOUT)
                response.raise_for_status()
                svg_content = response.text

                try:
                    os.makedirs(os.path.dirname(current_svg_cache_path), exist_ok=True)
                    with open(current_svg_cache_path, "w", encoding="utf-8") as f:
                        f.write(svg_content)
                    if verbose:
                        print(
                            f"      Downloaded and cached SVG: {os.path.relpath(current_svg_cache_path)}"
                        )
                except Exception as e:
                    if verbose:
                        print(
                            f"    Warning: Downloaded '{icon_obj.component_name}' but failed to cache SVG to {os.path.relpath(current_svg_cache_path)}: {e}",
                            file=sys.stderr,
                        )

            except requests.exceptions.RequestException as e:
                status_code_str = "N/A"
                if hasattr(e, "response") and e.response is not None:
                    status_code_str = str(e.response.status_code)
                error_msg = f"    Error: Failed to download SVG {icon_obj.component_name} (HTTP {status_code_str}): {url}"
                if verbose:
                    print(error_msg, file=sys.stderr)
                else:
                    _print_message_clean(error_msg, is_error=True)
                error_count += 1
                continue
            except Exception as e:
                error_msg = f"    Unexpected error during SVG download of {icon_obj.component_name}: {e}"
                if verbose:
                    print(error_msg, file=sys.stderr)
                else:
                    _print_message_clean(error_msg, is_error=True)
                error_count += 1
                continue

        if svg_content:
            if verbose:
                print(f"      Extracting SVG elements...")
            icon_obj.elements = core_icons.extract_svg_elements(svg_content)
            if icon_obj.elements:
                processed_icons_with_data.append(icon_obj)
                if verbose:
                    print(
                        f"      Successfully processed {len(icon_obj.elements)} SVG element(s)."
                    )
            else:
                msg = f"    Warning: No graphical SVG elements extracted for {icon_obj.component_name} from {url}."
                if verbose:
                    print(msg, file=sys.stderr)
                elif not silent:
                    _print_message_clean(msg, is_error=True)
                error_count += 1
        else:
            error_msg = f"    Error: No SVG content for {icon_obj.component_name} after download/cache attempt."
            if verbose:
                print(error_msg, file=sys.stderr)
            else:
                _print_message_clean(error_msg, is_error=True)
            error_count += 1

    if not verbose and not silent and total_icons > 0 and last_print_len > 0:
        print("\r" + " " * last_print_len + "\r", end="")
        sys.stdout.flush()

    return processed_icons_with_data, error_count
