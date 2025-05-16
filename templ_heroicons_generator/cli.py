# templ_heroicons_generator/cli.py

import argparse
import sys
import os
import requests # For requests.exceptions.RequestException in the top-level try-except
import traceback # For verbose error reporting

from .core import scanner
from .core import downloader
from .core import templ_builder
from .core import config # For default values for argparse and other constants


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
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument(
        "--input-dir", "-i", default=".",
        help="Root directory of the project containing .templ files to scan."
    )
    parser.add_argument(
        "--output-dir", "-o", default=config.DEFAULT_OUTPUT_DIR,
        help=(f"Output directory for '{config.OUTPUT_FILENAME}'. The Go package name is derived "
              "from this directory's base name.")
    )
    parser.add_argument(
        "--force", "-f", action="store_true",
        help="Overwrite the output file if it exists, even if content is identical."
    )
    parser.add_argument(
        "--exclude-output", type=lambda x: str(x).lower() not in ['false', '0', 'no'],
        default=True,
        help=("Exclude .templ files within the --output-dir from scanning. "
              "Use '--exclude-output false' to disable exclusion.")
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
        "--default-class", default=config.DEFAULT_SVG_CLASS,
        help="Default CSS class attribute value for SVG elements."
    )
    parser.add_argument(
        "--cache-dir", default=config.DEFAULT_CACHE_DIR,
        help="Directory to store cached SVG files."
    )
    return parser.parse_args()


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
        if args.verbose:
            print("Verbose mode enabled.")
            # To print arguments if needed for debugging, consider:
            # print(f"Script arguments: {vars(args)}")

        print("Fetching available Heroicons list from GitHub API...")
        valid_icons_list = downloader.fetch_heroicons_list(args.verbose)
        if not valid_icons_list and args.verbose:
            print("  Warning: Could not fetch or parse the list of available icons. "
                  "Validation against the official list will be skipped.", file=sys.stderr)
        elif valid_icons_list and args.verbose:
            print("  Icon list fetched successfully.")

        if args.verbose: print("Scanning project for icon usage...")
        icons_to_generate = scanner.find_used_icons(
            input_dir=args.input_dir,
            output_dir_to_exclude=args.output_dir,
            exclude_output_dir_files=args.exclude_output,
            verbose=args.verbose,
            valid_icons_list=valid_icons_list
        )

        if not icons_to_generate and not args.dry_run:
            print("No icons found in project files matching the required format, or none were valid.")

        if args.verbose and icons_to_generate:
            print(f"Preparing to download/cache SVGs for {len(icons_to_generate)} icon(s)...")
        elif args.verbose and not icons_to_generate:
            print("No icons to download/cache.")

        valid_icons_data, download_errors = downloader.download_svgs(
            icons_to_process=icons_to_generate,
            verbose=args.verbose,
            cache_dir=args.cache_dir
        )

        if download_errors > 0:
            print(f"\nWarning: Encountered {download_errors} error(s) during SVG download/processing.", file=sys.stderr)
            if not valid_icons_data and icons_to_generate and not args.dry_run:
                print("  Error: Failed to process any identified icons. Cannot generate package.", file=sys.stderr)
                # No sys.exit here; let it fall through to finally block with non-zero exit_code
                exit_code = 1 # Mark as error, but proceed to finally
                # To exit immediately, you could do: sys.exit(1) but the finally block is cleaner
                # For now, we will let it try to generate an empty package if it reaches that far.
                # However, if it's a critical failure, it might be better to exit.
                # Let's assume we want to try generating anyway if some data might exist.
                # If exit_code is set, the final message will reflect an error.
            elif icons_to_generate and args.verbose:
                 print(f"  Proceeding with {len(valid_icons_data)} successfully processed icon(s).", file=sys.stderr)
        
        # Only proceed to generate if no critical error has occurred that should stop us
        if exit_code == 0:
            if args.verbose: print("Generating Templ package...")
            generated_content = templ_builder.generate_heroicons_package(
                output_dir=args.output_dir,
                icons=valid_icons_data,
                force=args.force,
                verbose=args.verbose,
                dry_run=args.dry_run,
                default_class=args.default_class
            )

            if args.dry_run:
                if generated_content:
                    target_path = os.path.join(args.output_dir, config.OUTPUT_FILENAME)
                    try:
                        rel_target_path = os.path.relpath(target_path)
                    except ValueError:
                        rel_target_path = target_path
                    print(f"\n--- Dry Run: Content that would be written to {rel_target_path} ---")
                    print(generated_content.strip())
                    print("--- End Dry Run ---")
                else:
                    print("\n--- Dry Run: No content was generated. ---")
        else:
            print("Skipping package generation due to previous errors.", file=sys.stderr)


    except SystemExit as e:
        # This can be raised by argparse --help/--version or by core modules if not refactored
        exit_code = e.code if isinstance(e.code, int) else 1
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.", file=sys.stderr)
        exit_code = 130
    except requests.exceptions.RequestException as e:
        print(f"\nNetwork Error: A critical network error occurred: {e}", file=sys.stderr)
        if args.verbose:
            traceback.print_exc(file=sys.stderr)
        exit_code = 1
    except FileNotFoundError as e:
        print(f"\nFile System Error: {e}", file=sys.stderr)
        if args.verbose:
            traceback.print_exc(file=sys.stderr)
        exit_code = 1
    except OSError as e:
        print(f"\nOS Error: {e}", file=sys.stderr)
        if args.verbose:
            traceback.print_exc(file=sys.stderr)
        exit_code = 1
    except IOError as e:
        print(f"\nI/O Error: {e}", file=sys.stderr)
        if args.verbose:
            traceback.print_exc(file=sys.stderr)
        exit_code = 1
    except RuntimeError as e:
        print(f"\nRuntime Error: {e}", file=sys.stderr)
        if args.verbose:
            traceback.print_exc(file=sys.stderr)
        exit_code = 1
    except Exception as e:
        print(f"\n--- Unexpected Error ---", file=sys.stderr)
        print(f"An unhandled error occurred: {e}", file=sys.stderr)
        print("\n--- Traceback ---", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        print("--- End Traceback ---", file=sys.stderr)
        exit_code = 1
    finally:
        if exit_code == 0:
            print("Script finished successfully.")
        else:
            print(f"Script finished with errors (exit code {exit_code}).")
        sys.exit(exit_code)

if __name__ == '__main__':
    main()