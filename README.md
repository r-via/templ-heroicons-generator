# Heroicons Templ Generator

This script (`generate_heroicons.py`) generates a `heroicons.templ` file for Go Templ projects, embedding Heroicons SVG icons as reusable Templ components optimized for production use. It scans `.templ` files for Heroicons usage, fetches the required SVG icons from the official Heroicons repository, caches them locally, and produces a Go package with direct SVG elements. The script ensures minimal dependencies, robust error handling, and features like dry-run mode and content change detection to avoid unnecessary file writes.

## Features

- **Automatic Icon Detection**: Scans `.templ` files recursively to identify Heroicons usage (e.g., `@heroicons.Outline_bars_3`).
- **SVG Fetching and Caching**: Downloads SVGs from the official Heroicons repository (`tailwindlabs/heroicons`) and caches them locally to minimize network requests.
- **Templ Component Generation**: Creates a `heroicons.templ` file with Go Templ components, embedding SVG elements (`path`, `circle`, `rect`, etc.) directly.
- **Production Optimization**: Generates components with `{ attrs... }` for flexibility and a fixed `class` attribute for consistent styling.
- **Dependency Management**: Automatically checks and installs required Python packages (`requests`, `jinja2`) using `importlib.metadata` (Python 3.8+).
- **Validation**: Fetches the list of available Heroicons to validate icon usage, warning about invalid or unknown icons.
- **Change Detection**: Skips writing the output file if its content hasn't changed, unless forced.
- **Configurable Options**: Supports customizable output directory, cache location, default SVG classes, and dry-run mode for previewing output.
- **Verbose Logging**: Provides detailed output for debugging and progress tracking.
- **Error Handling**: Robustly handles network issues, file errors, and parsing failures with clear error messages.

## Requirements

- **Python**: Version 3.8 or higher.
- **Dependencies**:
  - `requests`: For fetching SVGs and icon lists from GitHub.
  - `jinja2`: For rendering the Templ output file.
  - These are automatically installed if missing (requires `pip` and internet access).
- **Go Templ**: The output requires `templ` version 0.2.513 or later.
- **Internet Access**: Needed to fetch SVGs and the Heroicons list (unless fully cached).
- **Optional**: A GitHub personal access token (set as `GITHUB_TOKEN` environment variable) to avoid GitHub API rate limits.

## Installation

1. Ensure Python 3.8+ is installed:
   ```bash
   python3 --version
   ```

2. Clone or download this script (`generate_heroicons.py`) to your project directory.

3. The script will automatically install required Python packages (`requests`, `jinja2`) on first run, assuming `pip` is available and you have internet access.

   To manually install dependencies:
   ```bash
   pip install requests jinja2
   ```

## Usage

Run the script from your project directory:

```bash
python3 generate_heroicons.py [options]
```

### Command-Line Options

| Option                | Description                                                                 | Default Value                     |
|-----------------------|-----------------------------------------------------------------------------|-----------------------------------|
| `-i, --input-dir`     | Root directory to scan for `.templ` files.                                  | `.` (current directory)           |
| `-o, --output-dir`    | Output directory for `heroicons.templ`. Package name is derived from this.   | `./components/heroicons`          |
| `-f, --force`         | Overwrite the output file even if content is identical.                     | `False`                           |
| `--exclude-output`    | Exclude `.templ` files in the output directory from scanning (`true/false`). | `True`                            |
| `-v, --verbose`       | Enable detailed output for scanning and downloading.                        | `False`                           |
| `--dry-run`           | Preview the generated output without writing to disk.                       | `False`                           |
| `--default-class`     | Default CSS class for SVG elements.                                         | `size-6`                          |
| `--cache-dir`         | Directory to store cached SVG files.                                        | `./.heroicons_cache`              |

### Example Commands

- Basic usage (scan current directory, output to `./components/heroicons`):
  ```bash
  python3 generate_heroicons.py
  ```

- Specify input and output directories:
  ```bash
  python3 generate_heroicons.py --input-dir ./src --output-dir ./generated
  ```

- Preview output without writing (dry run):
  ```bash
  python3 generate_heroicons.py --dry-run
  ```

- Force overwrite with verbose output:
  ```bash
  python3 generate_heroicons.py --force --verbose
  ```

- Use a custom cache directory and SVG class:
  ```bash
  python3 generate_heroicons.py --cache-dir ./cache --default-class "h-6 w-6"
  ```

### Environment Variables

- `GITHUB_TOKEN`: Optional. A GitHub personal access token to bypass API rate limits when fetching the Heroicons list. Example:
  ```bash
  export GITHUB_TOKEN=your_token_here
  python3 generate_heroicons.py
  ```

## Output

The script generates a `heroicons.templ` file in the specified output directory (default: `./components/heroicons`). This file contains:

- A Go package definition (package name derived from the output directory's basename, or `heroicons` if invalid).
- Templ components for each detected icon, with:
  - SVG elements (`path`, `circle`, etc.) extracted from the Heroicons SVGs.
  - Attributes like `xmlns`, `viewBox`, `fill`, `stroke`, and a default `class` (e.g., `size-6`).
  - Support for additional attributes via `{ attrs... }`.
- Comments indicating the source (Heroicons repository) and version (`master`).

Example output for `Outline_bars_3`:

```go
// Code generated by generate_heroicons.py. DO NOT EDIT.
// Source: https://raw.githubusercontent.com/tailwindlabs/heroicons/master/optimized/24
// Version: master
package heroicons

// Requires: templ v0.2.513 or later
// Web: https://heroicons.com/

// Outline_bars_3 renders the 'bars-3' icon (outline style).
// Source: https://raw.githubusercontent.com/tailwindlabs/heroicons/master/optimized/24/outline/bars-3.svg
templ Outline_bars_3(attrs templ.Attributes) {
	<svg
		xmlns="http://www.w3.org/2000/svg"
		fill="none"
		viewBox="0 0 24 24"
		stroke-width="1.5"
		stroke="currentColor"
		class="size-6"
		{ attrs... }
	>
		<path
			stroke-linecap="round"
			stroke-linejoin="round"
			d="M3.75 6.75h16.5M3.75 12h16.5m-16.5 5.25h16.5"
		/>
	</svg>
}
```

## How It Works

1. **Dependency Check**: Verifies and installs `requests` and `jinja2` using `importlib.metadata`.
2. **Icon Detection**: Scans `.templ` files for patterns like `@heroicons.Outline_bars_3`, validating against the Heroicons repository's icon list.
3. **SVG Fetching**: Downloads SVGs from `https://raw.githubusercontent.com/tailwindlabs/heroicons/master/optimized/24/{style}/{icon}.svg`, caching them in the specified cache directory.
4. **SVG Parsing**: Extracts graphical elements (`path`, `circle`, etc.) using `xml.etree.ElementTree`, ignoring comments and XML declarations.
5. **Templ Generation**: Uses a Jinja2 template to render the `heroicons.templ` file, ensuring proper formatting and attribute escaping.
6. **Output Handling**: Writes the file only if content has changed (unless `--force` is used) or displays it for dry runs.

## Caching

SVGs are cached in the specified cache directory (default: `./.heroicons_cache`) using MD5-hashed URLs as filenames. This reduces network requests on subsequent runs. To refresh the cache, delete the cache directory or specific SVG files.

## Validation

The script fetches the list of available Heroicons from the GitHub API (`https://api.github.com/repos/tailwindlabs/heroicons/contents/optimized/24`) to validate icon names. If the fetch fails (e.g., due to network issues or rate limits), validation is skipped, and the script proceeds with minimal checks.

## Error Handling

- **File Errors**: Reports missing or unreadable `.templ` files.
- **Network Errors**: Handles timeouts, HTTP errors, and other network issues during SVG or icon list fetching.
- **Parsing Errors**: Skips icons with invalid SVG content or unknown styles/names.
- **Dependency Errors**: Attempts to install missing packages or provides instructions for manual installation.
- **Output Errors**: Fails gracefully if the output directory cannot be created or the file cannot be written.

## Limitations

- **Heroicons Version**: Fixed to the `master` branch of the Heroicons repository. Future versions may require updating `HEROICONS_VERSION` and `HEROICONS_BASE_URL`.
- **SVG Complexity**: Assumes Heroicons' simple SVG structure. Complex SVGs with nested groups or unsupported elements may lose attributes (e.g., transforms on `<g>`).
- **GitHub API Limits**: Without a `GITHUB_TOKEN`, the script may hit rate limits when fetching the icon list, causing validation to be skipped.
- **No Incremental Updates**: The entire `heroicons.templ` file is regenerated each run. Partial updates are not supported.
- **No TypeScript/JavaScript Support**: Generates Go Templ components only.

## Troubleshooting

- **"Dependency not found"**: Ensure `pip` is installed and you have internet access. Install manually with `pip install requests jinja2`.
- **"Failed to fetch icon list"**: Set a `GITHUB_TOKEN` environment variable or check your internet connection. Validation is skipped if this fails.
- **"No icons found"**: Verify that your `.templ` files use the correct format (e.g., `@heroicons.Outline_bars_3`) and are in the input directory.
- **"Failed to write output"**: Check permissions for the output directory or specify a different `--output-dir`.
- **"Invalid package name"**: The output directory's basename must be a valid Go package name (e.g., no spaces or special characters). Use a different `--output-dir` or accept the fallback name (`heroicons`).

## Contributing

Contributions are welcome! Please submit issues or pull requests for bug fixes, feature additions, or documentation improvements. Suggested enhancements:

- Support for specific Heroicons versions or branches.
- Handling of complex SVG groups with transforms.
- Incremental file updates to preserve manual edits.
- Additional output formats (e.g., TypeScript, React).

## License

This script is licensed under the MIT License. The generated `heroicons.templ` file includes Heroicons SVGs, which are licensed under the MIT License by Tailwind Labs (see [heroicons.com](https://heroicons.com/)).

## Acknowledgments

- **Heroicons**: Created by Tailwind Labs ([tailwindlabs/heroicons](https://github.com/tailwindlabs/heroicons)).
- **Go Templ**: A fast and simple templating engine for Go ([github.com/a-h/templ](https://github.com/a-h/templ)).

For questions or support, open an issue on the repository or contact the maintainer.
