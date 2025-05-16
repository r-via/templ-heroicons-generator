# Templ Heroicons Generator

`templ-heroicons-generator` is a Python command-line tool that automates the creation of Go Templ components for [Heroicons](https://heroicons.com/), a collection of free, MIT-licensed SVG icons from the creators of Tailwind CSS.

The tool performs the following key actions:
1.  Recursively scans `.templ` files in your project to detect Heroicons usage (e.g., `@heroicons.Outline_check_circle`).
2.  Downloads the corresponding optimized 24x24 SVGs from the official Heroicons GitHub repository (`tailwindlabs/heroicons/optimized/24/{style}`).
3.  Caches these SVGs locally to avoid redundant downloads on subsequent runs.
4.  Optionally validates detected icon names against the official list fetched from the GitHub API.
5.  Generates a Go Templ file (e.g., `heroicons.templ`) containing Templ components for each *used* icon. These components embed the SVG's graphical elements (`<path>`, `<circle>`, `<rect>`, `<g>`, etc.) directly.
6.  The generated components use `{ attrs... }` for passing custom SVG attributes and include a customizable default CSS class (e.g., `size-6`).

The resulting Go package is minimal, containing only the icons actively used in your project, and is optimized for seamless integration into Go applications using the [Templ](https://templ.guide/) HTML templating engine. Icon component names are formatted with underscores and initial capitalization (e.g., `Outline_bars_3` for the SVG file `bars-3.svg`) for Go export compatibility and ease of maintenance.

## Key Features

-   **Automatic Icon Detection**: Identifies Heroicons used in `.templ` files with a syntax like `@heroicons.Outline_bars_3`.
-   **Optimized SVG Downloading**: Fetches optimized 24x24 SVGs from the official Heroicons repository.
-   **Local Caching**: Stores downloaded SVGs in a local cache directory (customizable, default: `./.heroicons_cache`) to minimize network requests and speed up subsequent runs.
-   **Icon Validation (Optional)**: Verifies the existence of icons against the GitHub API to prevent errors from typos or non-existent icons. Validation is skipped if the API is unreachable.
-   **Full SVG Element Support**: Includes all relevant SVG graphical elements (`<path>`, `<circle>`, `<rect>`, `<g>`, etc.) in the generated Templ components.
-   **Dry-Run Mode**: Allows previewing the generated output in the console without writing any files to disk (`--dry-run`).
-   **Customizable Default Class**: Define a fixed default CSS class for all generated SVG components via the `--default-class` option.
-   **Dynamic Go Package Naming**: The Go package name for the generated file is derived from the base name of the output directory (e.g., `myicons` if output is to `./components/myicons/`). Defaults to `heroicons` if the derived name is invalid.
-   **Recursive Scanning**: Traverses all `.templ` files within the specified input project directory, including subdirectories.
-   **Output Directory Exclusion**: By default, avoids scanning `.templ` files within the specified output directory itself.
-   **Comprehensive Customization**: Supports command-line arguments for input/output directories, cache location, force overwrite, verbosity, and more.
-   **Change Detection**: Skips rewriting the output file if its content has not changed (unless `--force` is used), playing well with build systems.
-   **Verbose Logging**: Provides detailed output for debugging and tracking the generation process (`-v, --verbose`).
-   **Robust Error Handling**: Gracefully handles network issues, file errors, and SVG parsing failures.

## Requirements

-   **Python**: Version 3.8 or higher.
-   **pip**: The Python package installer (usually comes with Python).
-   **Go Templ**: The generated output is intended for projects using [Go Templ](https://templ.guide/) (v0.2.513 or later recommended).
-   **Internet Access**: Required to initially fetch SVGs and the Heroicons list (unless all icons are already cached).
-   **Optional `GITHUB_TOKEN`**: A GitHub Personal Access Token (set as the `GITHUB_TOKEN` environment variable) can be used to increase API rate limits when fetching the Heroicons list.

## Installation

It's recommended to install `templ-heroicons-generator` within a Python virtual environment for your project.

1.  **Ensure Python 3.8+ and pip are installed and accessible.**
    ```bash
    python3 --version
    pip --version
    ```

2.  **Install the package using pip directly from GitHub:**
    ```bash
    pip install git+https://github.com/r-via/templ-heroicons-generator.git
    ```
    *(To install a specific version or branch, append `@tag_or_branch` to the URL, e.g., `...@v0.1.0`)*

    This command will download the package, build it if necessary, and install it along with its Python dependencies (`requests` and `jinja2`) into your active Python environment.

3.  **Verify the installation:**
    The command-line tool `templ-generate-heroicons` should now be available in your PATH (if your Python scripts directory is in PATH).
    ```bash
    templ-generate-heroicons --version
    # or to see all options:
    templ-generate-heroicons --help
    ```

**(For developing `templ-heroicons-generator` itself):**
If you've cloned the repository and want to install it in editable mode for development:
```bash
git clone https://github.com/r-via/templ-heroicons-generator.git
cd templ-heroicons-generator
pip install -e .
```

## Usage

After installation, run the `templ-generate-heroicons` command. It's typically run from the root of your Go project.

```bash
templ-generate-heroicons [OPTIONS]
```

### Command-Line Options

| Option                | Short | Description                                                                                                   | Default Value                     |
| :-------------------- | :---- | :------------------------------------------------------------------------------------------------------------ | :-------------------------------- |
| `--input-dir`         | `-i`  | Root directory of your project to scan for `.templ` files.                                                    | `.` (current directory)           |
| `--output-dir`        | `-o`  | Output directory for the generated `heroicons.templ` file. The Go package name is derived from this directory. | `./components/heroicons`          |
| `--force`             | `-f`  | Overwrite the output file even if its content has not changed.                                                | `False` (Off)                     |
| `--exclude-output`    |       | Exclude `.templ` files within the `--output-dir` from scanning. Use `--exclude-output false` to disable.      | `True` (On)                       |
| `--verbose`           | `-v`  | Enable detailed verbose output during scanning, downloading, and generation.                                  | `False` (Off)                     |
| `--dry-run`           |       | Preview the generated output in the console without writing to disk.                                          | `False` (Off)                     |
| `--default-class`     |       | Default CSS class attribute value to apply to the root `<svg>` elements.                                        | `size-6`                          |
| `--cache-dir`         |       | Directory to store cached SVG icon files.                                                                     | `./.heroicons_cache`              |

### Example Commands

-   **Generate icons (scan current directory, output to default location):**
    ```bash
    templ-generate-heroicons
    ```

-   **Specify input and output directories, and enable verbose logging:**
    ```bash
    templ-generate-heroicons --input-dir ./cmd/web/views --output-dir ./internal/web/components/heroicons --verbose
    ```

-   **Preview output without writing to disk (dry run):**
    ```bash
    templ-generate-heroicons --dry-run
    ```

-   **Force overwrite the output file and use a custom default SVG class:**
    ```bash
    templ-generate-heroicons --force --default-class "icon w-6 h-6"
    ```

### Environment Variables

-   **`GITHUB_TOKEN`**: (Optional) Your GitHub Personal Access Token. If this environment variable is set, the tool will use it for authenticated requests to the GitHub API when fetching the list of available Heroicons. This helps avoid rate limits, especially in CI/CD environments or for frequent use.
    ```bash
    export GITHUB_TOKEN="ghp_yourgithubtokenhere"
    templ-generate-heroicons
    ```

## Generated Output (`heroicons.templ`)

The tool generates a single Go Templ file (default name: `heroicons.templ`) in the specified `--output-dir`. This file will contain:

-   A Go `package` declaration. The package name is derived from the base name of the `--output-dir`. For example, if `--output-dir ./app/views/partials/icons` is used, the Go package name will be `icons`. If the derived name is not a valid Go package name, it defaults to `heroicons`.
-   Templ components for each unique Heroicon detected and successfully processed from your project.
    -   Component names follow the Go-exported format `Style_IconName` (e.g., `Outline_Bars_3`, `Solid_CheckCircle`).
    -   SVGs include standard attributes like `xmlns`, `viewBox`, and style-specific attributes (`fill="none"` and `stroke="currentColor"` for outline; `fill="currentColor"` for solid).
    -   The configured default CSS class (e.g., `class="size-6"`) is applied to the root `<svg>` tag.
    -   Components accept `templ.Attributes` via the `{ attrs... }` spread, allowing you to pass custom attributes (like a different `class`, `aria-label`, `id`, etc.) when calling the component.
-   Header comments indicating that the file is auto-generated, the source of the Heroicons, and the version used (currently `master` branch).

### Example Generated Component (`Outline_Trash`)

If your `.templ` files contain `@heroicons.Outline_trash`, the generated `heroicons.templ` (inside a package, say, `myicons`) would include:

```go
// Code generated by templ-heroicons-generator. DO NOT EDIT.
// Source: https://raw.githubusercontent.com/tailwindlabs/heroicons/master/optimized/24
// Version: master
package myicons // Or your derived package name

// Requires: templ v0.2.513 or later (Refer to https://templ.guide/project-setup/installation)
// Heroicons: https://heroicons.com/

// Outline_Trash renders the 'trash' icon (outline style).
// Source: https://raw.githubusercontent.com/tailwindlabs/heroicons/master/optimized/24/outline/trash.svg
templ Outline_Trash(attrs templ.Attributes) {
	<svg
		xmlns="http://www.w3.org/2000/svg"
		fill="none"
		viewBox="0 0 24 24"
		stroke-width="1.5"
		stroke="currentColor"
        { attrs... }
		class="size-6" // This is the --default-class
	>
		<path
			stroke-linecap="round"
			stroke-linejoin="round"
			d="m14.74 9-.346 9m-4.788 0L9.26 9m9.968-3.21c.342.052.682.107 1.022.166m-1.022-.165L18.16 19.673a2.25 2.25 0 0 1-2.244 2.077H8.084a2.25 2.25 0 0 1-2.244-2.077L4.772 5.79m14.456 0a48.108 48.108 0 0 0-3.478-.397m-12 .562c.34-.059.68-.114 1.022-.165m0 0a48.11 48.11 0 0 1 3.478-.397m7.5 0v-.916c0-1.18-.91-2.164-2.09-2.201a51.964 51.964 0 0 0-3.32 0c-1.18.037-2.09 1.022-2.09 2.201v.916m7.5 0a48.667 48.667 0 0 0-7.5 0"
		/>
	</svg>
}
```

## Integration with Your Go Templ Project

1.  **Generate the Icons**: Run `templ-generate-heroicons` with appropriate options for your project structure. For instance:
    ```bash
    templ-generate-heroicons -o ./views/components/heroicons
    ```
    This would create `./views/components/heroicons/heroicons.templ` with package name `heroicons`.

2.  **Import the Generated Package**: In your other `.templ` files where you want to use these icons, import the Go package that was generated. Assuming your Go module is `example.com/myproject` and you used the command above:
    ```go
    package mypage

    import "example.com/myproject/views/components/heroicons" // Import the generated package
    ```
    *(Note: `import "github.com/a-h/templ"` is not typically needed manually for component usage, as `templ generate` handles it.)*

3.  **Use the Icon Components**: Call the generated icon components like any other Templ component, passing attributes as needed.
    ```templatt
    templ MyPageComponent() {
        <button aria-label="Delete item">
            // Default class "size-6" will be applied
            @heroicons.Outline_Trash(templ.Attributes{})
        </button>
        <button aria-label="Edit item">
            // Override default class and add more
            @heroicons.Outline_PencilSquare(templ.Attributes{"class": "w-5 h-5 text-blue-500", "id": "edit-icon"})
        </button>
    }
    ```
    The `class` attribute passed via `attrs` will **replace** the default class defined in the component. If you want to *add* to the default class, you'd need to handle class merging in your Go code or use utility components, as `{ attrs... }` typically overwrites.

4.  **Compile Your Templ Files**: Run `templ generate` in your project.
    ```bash
    templ generate
    ```
    This will compile all your `.templ` files, including the generated `heroicons.templ` and the files that use its components, into Go code.

5.  **Build Your Go Application**:
    ```bash
    go build
    ```

### Example Integration (`admin_table.templ`)

Here's how you might use the generated icons in an example `admin_table.templ` file:

```go
package admin // Assuming this file is in ./views/admin/admin_table.templ

// Assuming your Go module is "example.com/myproject" and icons are in "./views/components/heroicons"
import "example.com/myproject/views/components/heroicons"

type AdminItem struct {
    ID       string
    Name     string
    Email    string
    IsActive bool
}

templ AdminTable(items []AdminItem) {
    <div class="overflow-x-auto relative shadow-md sm:rounded-lg">
        <table class="w-full text-sm text-left text-gray-500 dark:text-gray-400">
            <thead class="text-xs text-gray-700 uppercase bg-gray-50 dark:bg-gray-700 dark:text-gray-400">
                <tr>
                    <th scope="col" class="py-3 px-6">Name</th>
                    <th scope="col" class="py-3 px-6">Email</th>
                    <th scope="col" class="py-3 px-6">Status</th>
                    <th scope="col" class="py-3 px-6">
                        <span class="sr-only">Actions</span>
                    </th>
                </tr>
            </thead>
            <tbody>
                for _, item := range items {
                    <tr class="bg-white border-b dark:bg-gray-800 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-600">
                        <td class="py-4 px-6 font-medium text-gray-900 whitespace-nowrap dark:text-white">{ item.Name }</td>
                        <td class="py-4 px-6">{ item.Email }</td>
                        <td class="py-4 px-6">{ StatusBadge(item.IsActive) }</td>
                        <td class="py-4 px-6 text-right space-x-2">
                            <a href={ templ.URL("/admin/edit/" + item.ID) } class="font-medium text-blue-600 dark:text-blue-500 hover:underline">
                                @heroicons.Outline_PencilSquare(templ.Attributes{"class": "w-5 h-5 inline-block", "aria-label": "Edit"})
                            </a>
                            <button type="button" class="font-medium text-red-600 dark:text-red-500 hover:underline" hx-post={ "/admin/delete/" + item.ID } hx-confirm="Are you sure?">
                                @heroicons.Outline_Trash(templ.Attributes{"class": "w-5 h-5 inline-block", "aria-label": "Delete"})
                            </button>
                        </td>
                    </tr>
                }
            </tbody>
        </table>
    </div>
}

templ StatusBadge(isActive bool) {
    if isActive {
        <span class="bg-green-100 text-green-800 text-xs font-semibold mr-2 px-2.5 py-0.5 rounded dark:bg-green-200 dark:text-green-900">Active</span>
    } else {
        <span class="bg-red-100 text-red-800 text-xs font-semibold mr-2 px-2.5 py-0.5 rounded dark:bg-red-200 dark:text-red-900">Inactive</span>
    }
}
```

## Available Icons & Naming

Heroicons offers a comprehensive set of icons in both `Outline` and `Solid` styles. The generator will only include components for icons it detects in your project.

Icon names in your `.templ` files must be prefixed with `Outline_` or `Solid_`, followed by the icon's name parts separated by underscores. The generator converts this to the appropriate SVG filename (e.g., `Outline_Check_Circle` or `Outline_check_circle` becomes `check-circle.svg` and is rendered as `templ Outline_Check_Circle(...)`).

**Example Icon Naming:**

| SVG Filename (e.g., in `outline/`) | Usage in `.templ`                     | Generated Templ Component Name |
| :--------------------------------- | :------------------------------------ | :----------------------------- |
| `academic-cap.svg`                 | `@heroicons.Outline_Academic_Cap`     | `Outline_Academic_Cap`         |
| `arrow-down-tray.svg`              | `@heroicons.Outline_Arrow_Down_Tray`  | `Outline_Arrow_Down_Tray`      |
| `check-circle.svg`                 | `@heroicons.Solid_Check_Circle`       | `Solid_Check_Circle`           |
| `bars-3-bottom-left.svg`           | `@heroicons.Outline_Bars_3_Bottom_Left` | `Outline_Bars_3_Bottom_Left`   |

For a complete visual list and the official names, please refer to:
-   The [Heroicons Official Website](https://heroicons.com/)
-   The `optimized/24/outline` and `optimized/24/solid` directories in the [Heroicons GitHub repository](https://github.com/tailwindlabs/heroicons/tree/master/optimized/24).

### Full Icon List with Probable Usage

The icons are organized by common UI categories to help you find what you need. Each icon is listed with its `Style_Name_Parts` format for use in your templates and its likely application.

| **Category**     | **Icon Name (`Style_Name_Parts`)**                                 | **Probable UI Usage**                                                                 |
| :--------------- | :----------------------------------------------------------------- | :------------------------------------------------------------------------------------ |
| **Navigation & Arrows** | `Outline_Arrow_Down`, `Solid_Arrow_Down`                           | Indicate downward direction, dropdowns, scrolling.                                     |
|                  | `Outline_Arrow_Left`, `Solid_Arrow_Left`                           | Indicate leftward direction, "back" navigation.                                         |
|                  | `Outline_Arrow_Right`, `Solid_Arrow_Right`                         | Indicate rightward direction, "forward" or "next" navigation.                         |
|                  | `Outline_Arrow_Up`, `Solid_Arrow_Up`                               | Indicate upward direction, "scroll to top", collapsing sections.                       |
|                  | `Outline_Arrow_Uturn_Down`, `Solid_Arrow_Uturn_Down`               | U-turn down, often for "reply all" or redirecting flow downwards.                     |
|                  | `Outline_Arrow_Uturn_Left`, `Solid_Arrow_Uturn_Left`               | U-turn left, "undo" or return action.                                                  |
|                  | `Outline_Arrow_Uturn_Right`, `Solid_Arrow_Uturn_Right`             | U-turn right, "redo" or redirecting flow rightwards.                                   |
|                  | `Outline_Arrow_Uturn_Up`, `Solid_Arrow_Uturn_Up`                   | U-turn up, redirecting flow upwards.                                                   |
|                  | `Outline_Arrow_Long_Down`, `Solid_Arrow_Long_Down`                 | Longer arrow down, emphasize strong downward movement or sorting.                       |
|                  | `Outline_Arrow_Long_Left`, `Solid_Arrow_Long_Left`                 | Longer arrow left, emphasize significant backward navigation.                           |
|                  | `Outline_Arrow_Long_Right`, `Solid_Arrow_Long_Right`               | Longer arrow right, emphasize significant forward navigation.                            |
|                  | `Outline_Arrow_Long_Up`, `Solid_Arrow_Long_Up`                     | Longer arrow up, emphasize strong upward movement.                                      |
|                  | `Outline_Arrow_Down_Circle`, `Solid_Arrow_Down_Circle`             | Arrow down within a circle, download action or section expansion.                       |
|                  | `Outline_Arrow_Left_Circle`, `Solid_Arrow_Left_Circle`             | Arrow left within a circle, "previous" button in carousels or steps.                    |
|                  | `Outline_Arrow_Right_Circle`, `Solid_Arrow_Right_Circle`           | Arrow right within a circle, "next" button in carousels or steps.                       |
|                  | `Outline_Arrow_Up_Circle`, `Solid_Arrow_Up_Circle`                 | Arrow up within a circle, "back to top" button.                                        |
|                  | `Outline_Arrow_Down_Left`, `Solid_Arrow_Down_Left`                 | Diagonal arrow, specific directional cues or "bottom-left" actions.                    |
|                  | `Outline_Arrow_Down_Right`, `Solid_Arrow_Down_Right`               | Diagonal arrow, specific directional cues or "bottom-right" actions.                   |
|                  | `Outline_Arrow_Up_Left`, `Solid_Arrow_Up_Left`                     | Diagonal arrow, specific directional cues or "top-left" actions.                       |
|                  | `Outline_Arrow_Up_Right`, `Solid_Arrow_Up_Right`                   | Diagonal arrow, specific directional cues or "top-right" actions.                      |
|                  | `Outline_Arrow_Top_Right_On_Square`, `Solid_Arrow_Top_Right_On_Square` | "External link" or "open in new window".                                                 |
|                  | `Outline_Arrow_Trending_Down`, `Solid_Arrow_Trending_Down`         | Indicates a downward trend, for charts, analytics, finance.                           |
|                  | `Outline_Arrow_Trending_Up`, `Solid_Arrow_Trending_Up`             | Indicates an upward trend, for charts, analytics, finance.                             |
|                  | `Outline_Arrows_Pointing_In`, `Solid_Arrows_Pointing_In`           | Arrows pointing inwards, "collapse", "zoom in", "merge".                               |
|                  | `Outline_Arrows_Pointing_Out`, `Solid_Arrows_Pointing_Out`         | Arrows pointing outwards, "expand", "zoom out", "fullscreen".                           |
|                  | `Outline_Arrows_Right_Left`, `Solid_Arrows_Right_Left`             | Arrows for horizontal exchange, "transfer", "compare", bi-directional sync.              |
|                  | `Outline_Arrows_Up_Down`, `Solid_Arrows_Up_Down`                   | Arrows for vertical exchange, "sort", "reorder", bi-directional sync.                    |
|                  | `Outline_Chevron_Down`, `Solid_Chevron_Down`                       | Chevron down, dropdown menus, expandable sections.                                       |
|                  | `Outline_Chevron_Left`, `Solid_Chevron_Left`                       | Chevron left, "previous" in pagination, carousels, or side navigation.                  |
|                  | `Outline_Chevron_Right`, `Solid_Chevron_Right`                     | Chevron right, "next" in pagination, carousels, or indicating more content.             |
|                  | `Outline_Chevron_Up`, `Solid_Chevron_Up`                           | Chevron up, "scroll to top", collapsing sections.                                      |
|                  | `Outline_Chevron_Double_Down`, `Solid_Chevron_Double_Down`         | Double chevron down, "expand all", "go to end".                                       |
|                  | `Outline_Chevron_Double_Left`, `Solid_Chevron_Double_Left`         | Double chevron left, "go to first page", "fast backward".                               |
|                  | `Outline_Chevron_Double_Right`, `Solid_Chevron_Double_Right`       | Double chevron right, "go to last page", "fast forward".                                |
|                  | `Outline_Chevron_Double_Up`, `Solid_Chevron_Double_Up`             | Double chevron up, "collapse all", "go to beginning".                                   |
|                  | `Outline_Chevron_Up_Down`, `Solid_Chevron_Up_Down`                 | Up and down chevrons, sortable table header, selector.                                  |
|                  | `Outline_Bars_2`, `Solid_Bars_2`                                   | Two horizontal bars, compact menu or drag handle.                                        |
|                  | `Outline_Bars_3`, `Solid_Bars_3`                                   | Three horizontal bars, "hamburger" menu for navigation.                                  |
|                  | `Outline_Bars_3_Bottom_Left`, `Solid_Bars_3_Bottom_Left`           | Menu bars aligned bottom-left, specific UI layout control.                               |
|                  | `Outline_Bars_3_Bottom_Right`, `Solid_Bars_3_Bottom_Right`         | Menu bars aligned bottom-right, specific UI layout control.                              |
|                  | `Outline_Bars_3_Center_Left`, `Solid_Bars_3_Center_Left`           | Menu bars aligned center-left, specific UI layout control for sidebars.                    |
|                  | `Outline_Bars_4`, `Solid_Bars_4`                                   | Four horizontal bars, alternative menu or list view.                                     |
|                  | `Outline_Bars_Arrow_Down`, `Solid_Bars_Arrow_Down`                 | Menu bars with down arrow, sorting or filtering options (descending).                    |
|                  | `Outline_Bars_Arrow_Up`, `Solid_Bars_Arrow_Up`                     | Menu bars with up arrow, sorting or filtering options (ascending).                       |
|                  | `Outline_Ellipsis_Horizontal`, `Solid_Ellipsis_Horizontal`         | Three horizontal dots, "more options", "kebab menu".                                  |
|                  | `Outline_Ellipsis_Vertical`, `Solid_Ellipsis_Vertical`             | Three vertical dots, "more options", "meatball menu".                                   |
|                  | `Outline_Home`, `Solid_Home`                                       | Home, link to homepage or main dashboard.                                              |
|                  | `Outline_Home_Modern`, `Solid_Home_Modern`                         | Modern style home, real estate, contemporary dashboards.                                |
|                  | `Outline_Magnifying_Glass`, `Solid_Magnifying_Glass`               | Search functionality.                                                                   |
|                  | `Outline_Magnifying_Glass_Circle`, `Solid_Magnifying_Glass_Circle` | Search button or search within a specific context.                                      |
|                  | `Outline_Magnifying_Glass_Minus`, `Solid_Magnifying_Glass_Minus`   | Zoom out.                                                                               |
|                  | `Outline_Magnifying_Glass_Plus`, `Solid_Magnifying_Glass_Plus`     | Zoom in.                                                                                |
|                  | `Outline_Map`, `Solid_Map`                                         | Map, location services, addresses.                                                      |
|                  | `Outline_Map_Pin`, `Solid_Map_Pin`                                 | Map pin, mark a location, point of interest.                                           |
|                  | `Outline_Squares_2x2`, `Solid_Squares_2x2`                         | Grid view, app launcher, categories.                                                    |
|                  | `Outline_View_Columns`, `Solid_View_Columns`                       | Column view, layout switching.                                                          |
|                  | `Outline_List_Bullet`, `Solid_List_Bullet`                         | Bulleted list view.                                                                     |
| **Actions & Controls** | `Outline_Adjustments_Horizontal`, `Solid_Adjustments_Horizontal`   | Horizontal adjustments, filters, settings.                                               |
|                  | `Outline_Adjustments_Vertical`, `Solid_Adjustments_Vertical`     | Vertical adjustments, filters, settings.                                                 |
|                  | `Outline_Archive_Box`, `Solid_Archive_Box`                         | Archive item.                                                                           |
|                  | `Outline_Archive_Box_Arrow_Down`, `Solid_Archive_Box_Arrow_Down`   | Download from archive.                                                                  |
|                  | `Outline_Archive_Box_X_Mark`, `Solid_Archive_Box_X_Mark`           | Delete from archive.                                                                    |
|                  | `Outline_Arrow_Down_Tray`, `Solid_Arrow_Down_Tray`                 | Download.                                                                               |
|                  | `Outline_Arrow_Up_Tray`, `Solid_Arrow_Up_Tray`                     | Upload.                                                                                 |
|                  | `Outline_Backspace`, `Solid_Backspace`                             | Delete previous character, clear input.                                                  |
|                  | `Outline_Bookmark`, `Solid_Bookmark`                               | Bookmark item, save for later.                                                          |
|                  | `Outline_Bookmark_Slash`, `Solid_Bookmark_Slash`                   | Remove bookmark.                                                                        |
|                  | `Outline_Bookmark_Square`, `Solid_Bookmark_Square`                 | Bookmark within a squared context.                                                      |
|                  | `Outline_Check`, `Solid_Check`                                     | Confirmation, selection, completion.                                                    |
|                  | `Outline_Check_Badge`, `Solid_Check_Badge`                         | Verified status, achievement badge.                                                     |
|                  | `Outline_Check_Circle`, `Solid_Check_Circle`                       | Success, validation, task completed (circular context).                                  |
|                  | `Outline_Clipboard`, `Solid_Clipboard`                             | Copy to clipboard.                                                                      |
|                  | `Outline_Clipboard_Document`, `Solid_Clipboard_Document`           | Paste from clipboard, document actions.                                                 |
|                  | `Outline_Clipboard_Document_Check`, `Solid_Clipboard_Document_Check` | Document copied/validated.                                                              |
|                  | `Outline_Clipboard_Document_List`, `Solid_Clipboard_Document_List` | List of copied documents/items.                                                         |
|                  | `Outline_Cog`, `Solid_Cog`                                         | Settings, configuration (generic gear).                                                 |
|                  | `Outline_Cog_6_Tooth`, `Solid_Cog_6_Tooth`                         | Settings, configuration (6-tooth gear).                                                 |
|                  | `Outline_Cog_8_Tooth`, `Solid_Cog_8_Tooth`                         | Settings, configuration (8-tooth gear).                                                 |
|                  | `Outline_Document_Plus`, `Solid_Document_Plus`                     | Add new document.                                                                       |
|                  | `Outline_Document_Minus`, `Solid_Document_Minus`                   | Remove document.                                                                        |
|                  | `Outline_Document_Duplicate`, `Solid_Document_Duplicate`           | Duplicate document.                                                                     |
|                  | `Outline_Eye`, `Solid_Eye`                                         | View, preview, show password.                                                           |
|                  | `Outline_Eye_Dropper`, `Solid_Eye_Dropper`                         | Color picker.                                                                           |
|                  | `Outline_Eye_Slash`, `Solid_Eye_Slash`                             | Hide, hide password, visibility off.                                                    |
|                  | `Outline_Folder_Plus`, `Solid_Folder_Plus`                         | Add new folder.                                                                         |
|                  | `Outline_Folder_Minus`, `Solid_Folder_Minus`                       | Remove folder.                                                                          |
|                  | `Outline_Folder_Arrow_Down`, `Solid_Folder_Arrow_Down`             | Download folder contents.                                                               |
|                  | `Outline_Funnel`, `Solid_Funnel`                                   | Filter.                                                                                 |
|                  | `Outline_Minus`, `Solid_Minus`                                     | Remove, decrease, collapse.                                                             |
|                  | `Outline_Minus_Circle`, `Solid_Minus_Circle`                       | Remove or delete action (circular context).                                              |
|                  | `Outline_Paint_Brush`, `Solid_Paint_Brush`                         | Design, customize, edit appearance.                                                      |
|                  | `Outline_Pencil`, `Solid_Pencil`                                   | Edit, modify.                                                                           |
|                  | `Outline_Pencil_Square`, `Solid_Pencil_Square`                     | Edit item in a list or table row.                                                       |
|                  | `Outline_Plus`, `Solid_Plus`                                       | Add, increase, expand, create new.                                                      |
|                  | `Outline_Plus_Circle`, `Solid_Plus_Circle`                         | Add or create new action (circular context).                                             |
|                  | `Outline_Printer`, `Solid_Printer`                                 | Print.                                                                                  |
|                  | `Outline_Scale`, `Solid_Scale`                                     | Balance, legal, weigh options.                                                          |
|                  | `Outline_Share`, `Solid_Share`                                     | Share content.                                                                          |
|                  | `Outline_Shield_Check`, `Solid_Shield_Check`                       | Security checked, verified, protected.                                                  |
|                  | `Outline_Shield_Exclamation`, `Solid_Shield_Exclamation`           | Security warning, alert.                                                                |
|                  | `Outline_Squares_Plus`, `Solid_Squares_Plus`                       | Add to grid, new dashboard widget.                                                      |
|                  | `Outline_Star`, `Solid_Star`                                       | Favorite, rating, bookmark.                                                             |
|                  | `Outline_Trash`, `Solid_Trash`                                     | Delete, remove item.                                                                    |
|                  | `Outline_User_Plus`, `Solid_User_Plus`                             | Add user, new account.                                                                  |
|                  | `Outline_User_Minus`, `Solid_User_Minus`                           | Remove user, deactivate account.                                                        |
|                  | `Outline_X_Mark`, `Solid_X_Mark`                                   | Close, cancel, remove, incorrect.                                                       |
|                  | `Outline_X_Circle`, `Solid_X_Circle`                               | Error, failure, close modal (circular context).                                          |
| **Media Controls** | `Outline_Backward`, `Solid_Backward`                               | Previous track/item, rewind.                                                            |
|                  | `Outline_Forward`, `Solid_Forward`                                 | Next track/item, fast-forward.                                                          |
|                  | `Outline_Pause`, `Solid_Pause`                                     | Pause media playback.                                                                   |
|                  | `Outline_Pause_Circle`, `Solid_Pause_Circle`                       | Pause button (circular).                                                                |
|                  | `Outline_Play`, `Solid_Play`                                       | Play media, start process.                                                              |
|                  | `Outline_Play_Circle`, `Solid_Play_Circle`                         | Play button (circular).                                                                 |
|                  | `Outline_Play_Pause`, `Solid_Play_Pause`                           | Toggle play/pause.                                                                      |
|                  | `Outline_Stop`, `Solid_Stop`                                       | Stop media playback.                                                                    |
|                  | `Outline_Stop_Circle`, `Solid_Stop_Circle`                         | Stop button (circular).                                                                 |
|                  | `Outline_Speaker_Wave`, `Solid_Speaker_Wave`                       | Audio on, volume.                                                                       |
|                  | `Outline_Speaker_X_Mark`, `Solid_Speaker_X_Mark`                   | Mute, audio off.                                                                        |
|                  | `Outline_Microphone`, `Solid_Microphone`                           | Record audio, voice input.                                                              |
|                  | `Outline_Video_Camera`, `Solid_Video_Camera`                       | Record video, video call.                                                               |
|                  | `Outline_Video_Camera_Slash`, `Solid_Video_Camera_Slash`           | Video off, stop video recording.                                                        |
|                  | `Outline_Photo`, `Solid_Photo`                                     | Image, gallery, picture.                                                                |
|                  | `Outline_Camera`, `Solid_Camera`                                   | Take photo, camera.                                                                     |
|                  | `Outline_No_Symbol`, `Solid_No_Symbol`                             | Forbidden, restrict, block.                                                             |
| **Objects & Items** | `Outline_Academic_Cap`, `Solid_Academic_Cap`                       | Education, learning, degree.                                                            |
|                  | `Outline_Banknotes`, `Solid_Banknotes`                             | Money, currency, payment.                                                               |
|                  | `Outline_Beaker`, `Solid_Beaker`                                   | Science, experiment, lab.                                                               |
|                  | `Outline_Bell`, `Solid_Bell`                                       | Notifications, alerts.                                                                  |
|                  | `Outline_Bell_Alert`, `Solid_Bell_Alert`                           | Important notification, critical alert.                                                 |
|                  | `Outline_Bell_Slash`, `Solid_Bell_Slash`                           | Mute notifications.                                                                     |
|                  | `Outline_Bell_Snooze`, `Solid_Bell_Snooze`                         | Snooze notification.                                                                    |
|                  | `Outline_Book_Open`, `Solid_Book_Open`                             | Read, documentation, learning material.                                                 |
|                  | `Outline_Briefcase`, `Solid_Briefcase`                             | Work, business, portfolio.                                                              |
|                  | `Outline_Building_Library`, `Solid_Building_Library`               | Library, institution, public building.                                                  |
|                  | `Outline_Building_Office`, `Solid_Building_Office`                 | Office, company building.                                                               |
|                  | `Outline_Building_Office_2`, `Solid_Building_Office_2`             | Alternate office building icon.                                                         |
|                  | `Outline_Building_Storefront`, `Solid_Building_Storefront`         | Store, shop, marketplace.                                                               |
|                  | `Outline_Cake`, `Solid_Cake`                                       | Birthday, celebration, dessert.                                                         |
|                  | `Outline_Calculator`, `Solid_Calculator`                           | Calculate, math, finance tool.                                                          |
|                  | `Outline_Calendar`, `Solid_Calendar`                               | Calendar, date, schedule.                                                               |
|                  | `Outline_Calendar_Days`, `Solid_Calendar_Days`                     | Date range, specific days in a calendar.                                                |
|                  | `Outline_Chart_Bar`, `Solid_Chart_Bar`                             | Bar chart, analytics, statistics.                                                       |
|                  | `Outline_Chart_Bar_Square`, `Solid_Chart_Bar_Square`               | Bar chart in a square, data report.                                                     |
|                  | `Outline_Chart_Pie`, `Solid_Chart_Pie`                             | Pie chart, analytics, statistics.                                                       |
|                  | `Outline_Chat_Bubble_Bottom_Center`, `Solid_Chat_Bubble_Bottom_Center` | Comment, chat message (centered tail).                                                  |
|                  | `Outline_Chat_Bubble_Bottom_Center_Text`, `Solid_Chat_Bubble_Bottom_Center_Text` | Comment with text (centered tail).                                                    |
|                  | `Outline_Chat_Bubble_Left`, `Solid_Chat_Bubble_Left`               | Chat message from left.                                                                 |
|                  | `Outline_Chat_Bubble_Left_Ellipsis`, `Solid_Chat_Bubble_Left_Ellipsis` | Typing indicator or truncated message from left.                                        |
|                  | `Outline_Chat_Bubble_Left_Right`, `Solid_Chat_Bubble_Left_Right`   | Conversation, discussion between two parties.                                           |
|                  | `Outline_Chat_Bubble_Oval_Left`, `Solid_Chat_Bubble_Oval_Left`     | Oval chat message from left.                                                            |
|                  | `Outline_Chat_Bubble_Oval_Left_Ellipsis`, `Solid_Chat_Bubble_Oval_Left_Ellipsis` | Oval typing indicator from left.                                                      |
|                  | `Outline_Clock`, `Solid_Clock`                                     | Time, schedule, history.                                                                |
|                  | `Outline_Cloud`, `Solid_Cloud`                                     | Cloud services, weather.                                                                |
|                  | `Outline_Cloud_Arrow_Down`, `Solid_Cloud_Arrow_Down`               | Download from cloud.                                                                    |
|                  | `Outline_Cloud_Arrow_Up`, `Solid_Cloud_Arrow_Up`                   | Upload to cloud.                                                                        |
|                  | `Outline_Code_Bracket`, `Solid_Code_Bracket`                       | Code, development, programming.                                                         |
|                  | `Outline_Code_Bracket_Square`, `Solid_Code_Bracket_Square`         | Code block, embed code.                                                                 |
|                  | `Outline_CommandLine`, `Solid_CommandLine`                         | Terminal, CLI, command prompt.                                                          |
|                  | `Outline_Computer_Desktop`, `Solid_Computer_Desktop`               | Desktop computer, workstation.                                                          |
|                  | `Outline_Cpu_Chip`, `Solid_Cpu_Chip`                               | Processor, hardware, technology.                                                        |
|                  | `Outline_Credit_Card`, `Solid_Credit_Card`                         | Payment, credit card, finance.                                                          |
|                  | `Outline_Cube`, `Solid_Cube`                                       | 3D object, package, module.                                                             |
|                  | `Outline_Cube_Transparent`, `Solid_Cube_Transparent`               | 3D model, transparent object, abstract concept.                                         |
|                  | `Outline_Currency_Bangladeshi`, `Solid_Currency_Bangladeshi`       | Taka (BDT) currency.                                                                    |
|                  | `Outline_Currency_Dollar`, `Solid_Currency_Dollar`                 | Dollar (USD, CAD, AUD, etc.) currency.                                                  |
|                  | `Outline_Currency_Euro`, `Solid_Currency_Euro`                     | Euro (EUR) currency.                                                                    |
|                  | `Outline_Currency_Pound`, `Solid_Currency_Pound`                   | Pound (GBP) currency.                                                                   |
|                  | `Outline_Currency_Rupee`, `Solid_Currency_Rupee`                   | Rupee (INR) currency.                                                                   |
|                  | `Outline_Currency_Yen`, `Solid_Currency_Yen`                       | Yen (JPY) currency.                                                                     |
|                  | `Outline_Device_Phone_Mobile`, `Solid_Device_Phone_Mobile`         | Smartphone, mobile device.                                                              |
|                  | `Outline_Device_Tablet`, `Solid_Device_Tablet`                     | Tablet device.                                                                          |
|                  | `Outline_Document`, `Solid_Document`                               | Generic document, file.                                                                 |
|                  | `Outline_Document_Arrow_Down`, `Solid_Document_Arrow_Down`         | Download document.                                                                      |
|                  | `Outline_Document_Arrow_Up`, `Solid_Document_Arrow_Up`             | Upload document.                                                                        |
|                  | `Outline_Document_Chart_Bar`, `Solid_Document_Chart_Bar`           | Report with bar chart, data document.                                                   |
|                  | `Outline_Document_Check`, `Solid_Document_Check`                   | Approved document, validated file.                                                      |
|                  | `Outline_Document_Magnifying_Glass`, `Solid_Document_Magnifying_Glass` | Search document, find in file.                                                        |
|                  | `Outline_Document_Text`, `Solid_Document_Text`                     | Text document, article.                                                                 |
|                  | `Outline_Envelope`, `Solid_Envelope`                               | Mail, email, message.                                                                   |
|                  | `Outline_Envelope_Open`, `Solid_Envelope_Open`                     | Read mail, opened email.                                                                |
|                  | `Outline_Film`, `Solid_Film`                                       | Movie, video content, cinema.                                                           |
|                  | `Outline_Fire`, `Solid_Fire`                                       | Hot, trending, urgent, delete permanently.                                              |
|                  | `Outline_Flag`, `Solid_Flag`                                       | Flag item, report, mark for attention.                                                  |
|                  | `Outline_Folder`, `Solid_Folder`                                   | Folder, directory.                                                                      |
|                  | `Outline_Folder_Open`, `Solid_Folder_Open`                         | Open folder.                                                                            |
|                  | `Outline_Gift`, `Solid_Gift`                                       | Present, reward, promotion.                                                             |
|                  | `Outline_Gift_Top`, `Solid_Gift_Top`                               | Gift box lid, reveal gift.                                                              |
|                  | `Outline_Globe_Alt`, `Solid_Globe_Alt`                             | Globe, international, language, web.                                                    |
|                  | `Outline_Globe_Americas`, `Solid_Globe_Americas`                   | Americas region on globe.                                                               |
|                  | `Outline_Globe_Asia_Australia`, `Solid_Globe_Asia_Australia`       | Asia/Australia region on globe.                                                         |
|                  | `Outline_Globe_Europe_Africa`, `Solid_Globe_Europe_Africa`         | Europe/Africa region on globe.                                                          |
|                  | `Outline_Hand_Raised`, `Solid_Hand_Raised`                         | Raise hand, volunteer, stop.                                                            |
|                  | `Outline_Hand_Thumb_Down`, `Solid_Hand_Thumb_Down`                 | Dislike, thumbs down, negative feedback.                                                |
|                  | `Outline_Hand_Thumb_Up`, `Solid_Hand_Thumb_Up`                     | Like, thumbs up, positive feedback, approval.                                           |
|                  | `Outline_Hashtag`, `Solid_Hashtag`                                 | Hashtag, topic, tag.                                                                    |
|                  | `Outline_Heart`, `Solid_Heart`                                     | Favorite, like, love, health.                                                           |
|                  | `Outline_Identification`, `Solid_Identification`                   | ID card, verification, profile.                                                         |
|                  | `Outline_Key`, `Solid_Key`                                         | Access, security, password, license key.                                                |
|                  | `Outline_Language`, `Solid_Language`                               | Language selection, translation.                                                        |
|                  | `Outline_Lifebuoy`, `Solid_Lifebuoy`                               | Help, support, assistance.                                                              |
|                  | `Outline_Light_Bulb`, `Solid_Light_Bulb`                           | Idea, tip, innovation, insight.                                                         |
|                  | `Outline_Link`, `Solid_Link`                                       | URL, hyperlink, attachment.                                                             |
|                  | `Outline_Lock_Closed`, `Solid_Lock_Closed`                         | Locked, secure, private.                                                                |
|                  | `Outline_Lock_Open`, `Solid_Lock_Open`                             | Unlocked, public, accessible.                                                           |
|                  | `Outline_Moon`, `Solid_Moon`                                       | Dark mode, night.                                                                       |
|                  | `Outline_Musical_Note`, `Solid_Musical_Note`                       | Music, audio, sound.                                                                    |
|                  | `Outline_Paper_Airplane`, `Solid_Paper_Airplane`                   | Send message, submit.                                                                   |
|                  | `Outline_Paper_Clip`, `Solid_Paper_Clip`                           | Attachment, attach file.                                                                |
|                  | `Outline_Phone`, `Solid_Phone`                                     | Phone call, contact.                                                                    |
|                  | `Outline_Phone_Arrow_Down_Left`, `Solid_Phone_Arrow_Down_Left`     | Incoming call, missed call.                                                             |
|                  | `Outline_Phone_Arrow_Up_Right`, `Solid_Phone_Arrow_Up_Right`       | Outgoing call, call placed.                                                             |
|                  | `Outline_Phone_X_Mark`, `Solid_Phone_X_Mark`                       | Hang up, decline call, end call.                                                        |
|                  | `Outline_Presentation_Chart_Bar`, `Solid_Presentation_Chart_Bar`   | Presentation with bar chart, business report.                                           |
|                  | `Outline_Presentation_Chart_Line`, `Solid_Presentation_Chart_Line` | Presentation with line chart, trends.                                                   |
|                  | `Outline_Puzzle_Piece`, `Solid_Puzzle_Piece`                       | Extension, add-on, module, integration.                                                 |
|                  | `Outline_Qr_Code`, `Solid_Qr_Code`                                 | QR code, scan for information.                                                          |
|                  | `Outline_Receipt_Percent`, `Solid_Receipt_Percent`                 | Discount, sale receipt.                                                                 |
|                  | `Outline_Receipt_Refund`, `Solid_Receipt_Refund`                   | Refund, return receipt.                                                                 |
|                  | `Outline_Rocket_Launch`, `Solid_Rocket_Launch`                     | Launch, new project, startup, boost.                                                    |
|                  | `Outline_Rss`, `Solid_Rss`                                         | RSS feed, subscription.                                                                 |
|                  | `Outline_Server`, `Solid_Server`                                   | Server, hosting, backend.                                                               |
|                  | `Outline_Server_Stack`, `Solid_Server_Stack`                       | Database, server cluster, stack.                                                        |
|                  | `Outline_Shopping_Bag`, `Solid_Shopping_Bag`                       | Purchases, orders, e-commerce bag.                                                      |
|                  | `Outline_Shopping_Cart`, `Solid_Shopping_Cart`                     | E-commerce cart, add to cart.                                                           |
|                  | `Outline_Signal`, `Solid_Signal`                                   | Network strength, connectivity.                                                         |
|                  | `Outline_Signal_Slash`, `Solid_Signal_Slash`                       | No signal, disconnected.                                                                |
|                  | `Outline_Sparkles`, `Solid_Sparkles`                               | New feature, AI, magic, highlights.                                                     |
|                  | `Outline_Sun`, `Solid_Sun`                                         | Light mode, daytime, brightness.                                                        |
|                  | `Outline_Table_Cells`, `Solid_Table_Cells`                         | Table view, spreadsheet, data grid.                                                     |
|                  | `Outline_Tag`, `Solid_Tag`                                         | Label, category, price tag.                                                             |
|                  | `Outline_Ticket`, `Solid_Ticket`                                   | Event ticket, support ticket, voucher.                                                  |
|                  | `Outline_Trophy`, `Solid_Trophy`                                   | Achievement, award, winner.                                                             |
|                  | `Outline_Tv`, `Solid_Tv`                                           | Television, display, media.                                                             |
|                  | `Outline_User`, `Solid_User`                                       | User profile, account, person.                                                          |
|                  | `Outline_User_Circle`, `Solid_User_Circle`                         | User avatar, user account (circular).                                                   |
|                  | `Outline_User_Group`, `Solid_User_Group`                           | Team, group of users, community.                                                        |
|                  | `Outline_Users`, `Solid_Users`                                     | Multiple users, audience.                                                               |
|                  | `Outline_Viewfinder_Circle`, `Solid_Viewfinder_Circle`             | Focus, target, scan, screenshot area.                                                   |
|                  | `Outline_Wallet`, `Solid_Wallet`                                   | Wallet, finance, digital currency.                                                      |
|                  | `Outline_Wifi`, `Solid_Wifi`                                       | Wi-Fi connection, wireless network.                                                     |
|                  | `Outline_Wrench`, `Solid_Wrench`                                   | Tools, repair, maintenance (simple).                                                    |
|                  | `Outline_Wrench_Screwdriver`, `Solid_Wrench_Screwdriver`           | Tools, settings, configuration (more complex).                                          |
| **Status & Information** | `Outline_At_Symbol`, `Solid_At_Symbol`                             | Email address, mention.                                                                 |
|                  | `Outline_Bolt`, `Solid_Bolt`                                       | Lightning, fast, energy, action.                                                        |
|                  | `Outline_Bolt_Slash`, `Solid_Bolt_Slash`                           | Power off, energy saving.                                                               |
|                  | `Outline_Bug_Ant`, `Solid_Bug_Ant`                                 | Bug report, issue, debugging.                                                           |
|                  | `Outline_Chat_Bubble_Oval_Left_Ellipsis`, `Solid_Chat_Bubble_Oval_Left_Ellipsis` | Typing indicator, message pending (oval).                                               |
|                  | `Outline_Exclamation_Circle`, `Solid_Exclamation_Circle`           | Warning, alert (circular).                                                              |
|                  | `Outline_Exclamation_Triangle`, `Solid_Exclamation_Triangle`       | Critical warning, error, danger (triangular).                                           |
|                  | `Outline_Information_Circle`, `Solid_Information_Circle`           | Information, help, details.                                                             |
|                  | `Outline_Question_Mark_Circle`, `Solid_Question_Mark_Circle`       | Help, FAQ, support query.                                                               |
|                  | `Outline_Variable`, `Solid_Variable`                               | Mathematical variable, programming variable, dynamic content.                             |
|                  | `Outline_Power`, `Solid_Power`                                     | Power on/off, logout, shutdown.                                                         |
|                  | `Outline_Arrow_Path`, `Solid_Arrow_Path`                           | Refresh, reload, retry, sync.                                                           |
|                  | `Outline_Arrow_Path_Rounded_Square`, `Solid_Arrow_Path_Rounded_Square` | Refresh/sync action within a button or specific UI element.                             |
|                  | `Outline_Cpu_Chip`, `Solid_Cpu_Chip`                               | Processing, computing, hardware status.                                                 |
|                  | `Outline_Ellipsis_Horizontal_Circle`, `Solid_Ellipsis_Horizontal_Circle` | Loading, pending, more options (circular horizontal).                                   |
|                  | `Outline_Megaphone`, `Solid_Megaphone`                             | Announcement, broadcast, marketing.                                                     |
|                  | `Outline_Radio`, `Solid_Radio`                                     | Live broadcast, radio signal, transmitting.                                             |

## Project Setup and Build Pipeline

1.  **Project Structure (Example)**:
    ```
    mygoproject/
    ├── go.mod
    ├── main.go
    ├── views/                  # Your .templ source files
    │   ├── pages/
    │   │   └── home.templ
    │   └── components/
    │       └── heroicons/      # Generated output directory
    │           └── heroicons.templ (generated by this tool)
    ├── .heroicons_cache/       # Cache directory
    │   └── ... (cached SVGs)
    └── Makefile (optional)
    ```

2.  **Makefile Integration (Optional)**:
    To integrate icon generation into your build process, you can add a target to your `Makefile`:
    ```makefile
    .PHONY: icons templ-generate go-build build

    # Define variables for directories if they are configurable
    TEMPL_SOURCE_DIR := ./views
    HEROICONS_OUTPUT_DIR := $(TEMPL_SOURCE_DIR)/components/heroicons
    CACHE_DIR := ./.heroicons_cache # Or another preferred location

    icons:
        @echo "Generating Heroicons Templ components..."
        templ-generate-heroicons -i $(TEMPL_SOURCE_DIR) -o $(HEROICONS_OUTPUT_DIR) --cache-dir $(CACHE_DIR)

    templ-generate: icons
        @echo "Compiling Templ files..."
        templ generate

    go-build:
        @echo "Building Go application..."
        go build -o myapp .

    build: templ-generate go-build
        @echo "Build complete."

    # To run:
    # make icons (to only generate icons)
    # make build (to generate icons, compile templ, and build Go app)
    ```

## Troubleshooting

-   **Command not found: `templ-generate-heroicons`**:
    -   Ensure the package was installed correctly via `pip`.
    -   Verify that the Python environment where you installed the package is active.
    -   Check if the `scripts` or `bin` directory of your Python environment is in your system's `PATH`.

-   **"Failed to fetch Heroicons list from GitHub API"**:
    -   Check your internet connection.
    -   You might be hitting GitHub API rate limits. Set the `GITHUB_TOKEN` environment variable.
    -   If fetching fails, the script skips remote validation of icon names. This is usually non-critical.

-   **No icons generated / "No icons found..."**:
    -   Verify correct syntax in `.templ` files: `@heroicons.Style_IconName` (e.g., `@heroicons.Outline_ArchiveBox`).
    -   Ensure `.templ` files are within `--input-dir`.
    -   Run with `--verbose` to see scanning details.

-   **"Error: Input directory '...' not found" / "Error: Could not create output directory '...'"**:
    -   Check that the paths are correct and you have necessary permissions.

-   **Warning about derived package name (e.g., "Using fallback 'heroicons'")**:
    -   The base name of your `--output-dir` must be a valid Go package name (e.g., `myicons`, not `my-icons`). Rename the directory or accept the fallback.

-   **Generated classes not merging with passed classes**:
    -   The `class` attribute provided via `{ attrs... }` *replaces* the default class in the SVG component. Example:
        `@heroicons.Outline_Trash(templ.Attributes{"class": "new-class"})` results in `class="new-class"`.
    -   If you need to *add* classes, you'll need to manage this in your Go Templ logic or use CSS to extend the base class. For advanced class merging, consider utility Templ components or helper functions in Go.

-   **Templ Compilation Errors**:
    -   Ensure you have a compatible version of `templ` installed (`templ version`).
    -   If errors point to `heroicons.templ`, check the generated file for syntax issues (though this should be rare). Use `--dry-run` to inspect the output if problems persist.

## Limitations and Considerations

-   **Heroicons Version**: Fetches from the `master` branch of Heroicons. Specific version targeting is not currently supported.
-   **SVG Complexity**: Optimized for Heroicons' structure. Highly complex SVGs or those using CSS-in-SVG might not render as expected. Group (`<g>`) attributes like `transform` are not directly preserved on the group itself.
-   **Generated File Overwritten**: Manual edits to `heroicons.templ` will be lost on the next run unless the "no changes detected" logic kicks in. It's best to treat this file as purely auto-generated.

## Contributing

Contributions are highly welcome! Please feel free to open an issue or submit a pull request for:
-   Bug fixes
-   Feature enhancements (e.g., specific Heroicons version support, improved SVG group handling)
-   Documentation improvements

Please check the [Issues page](https://github.com/r-via/templ-heroicons-generator/issues) on GitHub.

## License

`templ-heroicons-generator` is licensed under the MIT License. See the `LICENSE` file in the repository for full details.

The Heroicons themselves are an open-source SVG icon library created by [Tailwind Labs](https://tailwindcss.com/) and are also licensed under the MIT License. For more information, visit [heroicons.com](https://heroicons.com/) and their [GitHub repository](https://github.com/tailwindlabs/heroicons).

## Acknowledgments

-   **Heroicons** by Tailwind Labs.
-   **Go Templ** by Adrian Hirst and contributors.