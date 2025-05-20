# templ_heroicons_generator/core/utils.py

import re

def is_valid_go_package_name(name: str) -> bool:
    """
    Checks if a string is a syntactically valid Go package name.

    A valid Go package name must generally:
    1. Consist of lowercase letters, digits, and underscores.
    2. Start with a lowercase letter.
    3. Not be a Go keyword.
    4. Not be the blank identifier "_".

    This function implements a common interpretation of these rules. It does not
    cover all nuances of the Go language specification regarding identifiers (such
    as Unicode characters, which are permitted but less conventional for package names).

    Args:
        name: The string to validate as a Go package name.

    Returns:
        True if the name is considered a valid Go package name according to
        the implemented rules, False otherwise.
    """
    if not name:
        return False

    # A set of common Go keywords. This list might need updates if new keywords
    # are introduced in future Go versions, but covers standard reserved words.
    go_keywords = {
        "break", "case", "chan", "const", "continue",
        "default", "defer", "else", "fallthrough", "for",
        "func", "go", "goto", "if", "import",
        "interface", "map", "package", "range", "return",
        "select", "struct", "switch", "type", "var",
    }

    # Regular expression to check for valid characters and starting letter:
    # - Must start with a lowercase letter (^[a-z]).
    # - Followed by zero or more lowercase letters, digits, or underscores ([a-z0-9_]*$).
    if not re.match(r'^[a-z][a-z0-9_]*$', name):
        return False

    # Package name cannot be a keyword or the blank identifier.
    if name in go_keywords or name == "_":
        return False

    return True

# Add other general utility functions here if needed in the future.
# For example, functions for path normalization if more complex than os.path.normpath,
# or specific string manipulations not tied to other core modules.