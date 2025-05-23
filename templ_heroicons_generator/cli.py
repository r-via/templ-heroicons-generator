# templ_heroicons_generator/cli.py

import argparse
import sys
import os
import requests  # For requests.exceptions.RequestException in the top-level try-except
import traceback  # For verbose error reporting

from .core import scanner
from .core import downloader
from .core import templ_builder
from .core import config  # For default values for argparse and other constants


def parse_args() -> argparse.Namespace:
    """
    Parses command-line arguments for the Heroicons Templ generator.

    Defines and parses all available command-line options, providing default
    values from the `core.config` module where appropriate.

    Returns:
        An argparse.Namespace object containing the parsed command-line arguments.
    """
    parser = argparse.ArgumentParser(
        description="Generate a heroicons.templ file from used icons, optimized for production.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--input-dir",
        "-i",
        default=".",
        help="Root directory of the project containing .templ files to scan.",
    )
    parser.add_argument(
        "--output-dir",
        "-o",
        default=config.DEFAULT_OUTPUT_DIR,
        help=(
            f"Output directory for '{config.OUTPUT_FILENAME}'. The Go package name is derived "
            "from this directory's base name."
        ),
    )
    parser.add_argument(
        "--force",
        "-f",
        action="store_true",
        help="Overwrite the output file if it exists, even if content is identical.",
    )
    parser.add_argument(
        "--exclude-output",
        type=lambda x: str(x).lower() not in ["false", "0", "no"],
        default=True,
        help=(
            "Exclude .templ files within the --output-dir from scanning. "
            "Use '--exclude-output false' to disable exclusion."
        ),
    )

    # Verbosity and Silent group
    verbosity_group = parser.add_mutually_exclusive_group()
    verbosity_group.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable detailed verbose output, including crawled files, during scanning and downloading.",
    )
    verbosity_group.add_argument(
        "--silent",
        "-s",
        action="store_true",
        help="Suppress all informational output. Only errors will be printed. Overrides --verbose.",
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview the generated output without writing to disk.",
    )
    parser.add_argument(
        "--default-class",
        default=config.DEFAULT_SVG_CLASS,
        help="Default CSS class attribute value for SVG elements.",
    )
    parser.add_argument(
        "--cache-dir",
        default=config.DEFAULT_CACHE_DIR,
        help="Directory to store cached SVG files.",
    )
    args = parser.parse_args()

    # If silent is true, verbose must be false, regardless of user input for verbose
    if args.silent:
        args.verbose = False

    return args


def main():
    """
    Main function for the Command Line Interface.

    This function orchestrates the entire process of generating Heroicons Templ components:
    1. Parses command-line arguments.
    2. Fetches the list of available Heroicons for validation.
    3. Scans project files to find used icons.
    4. Downloads and caches SVG data for these icons.
    5. Generates the .templ Go package file.
    It also handles top-level error catching and program exit codes.
    """
    args = parse_args()
    exit_code = 0

    try:
        if args.verbose:  # This implies not args.silent
            print("Verbose mode enabled.")
            # print(f"Script arguments: {vars(args)}") # Uncomment for deep debugging

        if not args.silent:
            print("Fetching available Heroicons list from GitHub API...")

        valid_icons_list = downloader.fetch_heroicons_list(
            verbose=args.verbose,  # Pass verbose (which is false if silent is true)
            silent=args.silent,
        )
        if not valid_icons_list and args.verbose:  # verbose implies not silent
            print(
                "  Warning: Could not fetch or parse the list of available icons. "
                "Validation against the official list will be skipped.",
                file=sys.stderr,
            )
        elif valid_icons_list and args.verbose:  # verbose implies not silent
            print("  Icon list fetched successfully.")

        if args.verbose:
            print("Scanning project for icon usage...")  # verbose implies not silent
        icons_to_generate = scanner.find_used_icons(
            input_dir=args.input_dir,
            output_dir_to_exclude=args.output_dir,
            exclude_output_dir_files=args.exclude_output,
            verbose=args.verbose,  # Pass verbose
            silent=args.silent,  # Pass silent
            valid_icons_list=valid_icons_list,
        )

        if not icons_to_generate and not args.dry_run and not args.silent:
            print(
                "No icons found in project files matching the required format, or none were valid."
            )

        if args.verbose and icons_to_generate:  # verbose implies not silent
            print(
                f"Preparing to download/cache SVGs for {len(icons_to_generate)} icon(s)..."
            )
        elif args.verbose and not icons_to_generate:  # verbose implies not silent
            print("No icons to download/cache.")

        valid_icons_data, download_errors = downloader.download_svgs(
            icons_to_process=icons_to_generate,
            verbose=args.verbose,  # Pass verbose
            silent=args.silent,  # Pass silent
            cache_dir=args.cache_dir,
        )

        if download_errors > 0:
            # Errors should always be printed, even if silent
            print(
                f"\nWarning: Encountered {download_errors} error(s) during SVG download/processing.",
                file=sys.stderr,
            )
            if not valid_icons_data and icons_to_generate and not args.dry_run:
                print(
                    "  Error: Failed to process any identified icons. Cannot generate package.",
                    file=sys.stderr,
                )
                exit_code = 1
            elif icons_to_generate and args.verbose:  # verbose implies not silent
                print(
                    f"  Proceeding with {len(valid_icons_data)} successfully processed icon(s).",
                    file=sys.stderr,
                )

        if exit_code == 0:
            if args.verbose:
                print("Generating Templ package...")  # verbose implies not silent
            generated_content = templ_builder.generate_heroicons_package(
                output_dir=args.output_dir,
                icons=valid_icons_data,
                force=args.force,
                verbose=args.verbose,  # Pass verbose
                silent=args.silent,  # Pass silent
                dry_run=args.dry_run,
                default_class=args.default_class,
            )

            if args.dry_run:
                if generated_content:
                    target_path = os.path.join(args.output_dir, config.OUTPUT_FILENAME)
                    try:
                        rel_target_path = os.path.relpath(target_path)
                    except ValueError:
                        rel_target_path = target_path
                    # Dry run output should appear even if silent, as it's the primary purpose of the flag
                    print(
                        f"\n--- Dry Run: Content that would be written to {rel_target_path} ---"
                    )
                    print(generated_content.strip())
                    print("--- End Dry Run ---")
                else:  # Dry run output
                    print("\n--- Dry Run: No content was generated. ---")
        else:  # Errors occurred
            print(
                "Skipping package generation due to previous errors.", file=sys.stderr
            )

    except SystemExit as e:
        exit_code = e.code if isinstance(e.code, int) else 1
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.", file=sys.stderr)
        exit_code = 130
    except requests.exceptions.RequestException as e:
        print(
            f"\nNetwork Error: A critical network error occurred: {e}", file=sys.stderr
        )
        if args.verbose:  # verbose implies not silent for traceback
            traceback.print_exc(file=sys.stderr)
        exit_code = 1
    except FileNotFoundError as e:
        print(f"\nFile System Error: {e}", file=sys.stderr)
        if args.verbose:  # verbose implies not silent
            traceback.print_exc(file=sys.stderr)
        exit_code = 1
    except OSError as e:
        print(f"\nOS Error: {e}", file=sys.stderr)
        if args.verbose:  # verbose implies not silent
            traceback.print_exc(file=sys.stderr)
        exit_code = 1
    except IOError as e:
        print(f"\nI/O Error: {e}", file=sys.stderr)
        if args.verbose:  # verbose implies not silent
            traceback.print_exc(file=sys.stderr)
        exit_code = 1
    except RuntimeError as e:
        print(f"\nRuntime Error: {e}", file=sys.stderr)
        if args.verbose:  # verbose implies not silent
            traceback.print_exc(file=sys.stderr)
        exit_code = 1
    except Exception as e:
        print(f"\n--- Unexpected Error ---", file=sys.stderr)
        print(f"An unhandled error occurred: {e}", file=sys.stderr)
        print("\n--- Traceback ---", file=sys.stderr)
        traceback.print_exc(
            file=sys.stderr
        )  # Always print traceback for unexpected errors
        print("--- End Traceback ---", file=sys.stderr)
        exit_code = 1
    finally:
        if not args.silent:
            if exit_code == 0:
                print("Script finished successfully.")
            else:
                print(f"Script finished with errors (exit code {exit_code}).")
        sys.exit(exit_code)


if __name__ == "__main__":
    main()
