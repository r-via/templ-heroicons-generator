# templ_heroicons_generator/core/config.py

"""
Default configuration constants for the templ-heroicons-generator.

This module defines default values used throughout the application,
such as default directory names, Heroicons API details, and CSS classes.
These values can often be overridden by command-line arguments.
"""

# --- Output Configuration ---
DEFAULT_OUTPUT_DIR: str = "./components/heroicons"
"""Default directory where the generated 'heroicons.templ' file will be placed."""

OUTPUT_FILENAME: str = "heroicons.templ"
"""The standard filename for the generated Templ component file."""

DEFAULT_FALLBACK_PACKAGE_NAME: str = "heroicons"
"""Default Go package name to use if it cannot be derived from the output directory."""

# --- Cache Configuration ---
DEFAULT_CACHE_DIR: str = "./.heroicons_cache"
"""Default directory for storing cached SVG icon files."""

# --- SVG/Templ Configuration ---
DEFAULT_SVG_CLASS: str = "size-6"
"""Default CSS class applied to the root <svg> element in generated components."""

# --- Heroicons Source Configuration ---
HEROICONS_VERSION: str = "master"
"""The Git branch or tag of the tailwindlabs/heroicons repository to use (e.g., 'master', 'v2.0.13')."""

HEROICONS_BASE_URL: str = f"https://raw.githubusercontent.com/tailwindlabs/heroicons/{HEROICONS_VERSION}/optimized/24"
"""Base URL for fetching individual optimized 24x24 SVG icons."""

HEROICONS_LIST_URL: str = f"https://api.github.com/repos/tailwindlabs/heroicons/contents/optimized/24"
"""GitHub API URL for fetching the list of available 24x24 icons in 'outline' and 'solid' styles."""

# --- Network Configuration ---
REQUEST_TIMEOUT: int = 15
"""Timeout in seconds for HTTP requests (e.g., fetching icon lists or SVGs)."""

# --- Icon Regex Pattern (Used by scanner.py) ---
# This could also reside in scanner.py if it's solely used there,
# but placing it here makes it a central piece of "configuration" for how icons are identified.
ICON_USAGE_PATTERN: str = r'@heroicons\.([A-Z_a-z][a-zA-Z0-9_]+)\b'
"""Regex pattern to identify Heroicon usage in .templ files (e.g., @heroicons.Outline_bars_3)."""