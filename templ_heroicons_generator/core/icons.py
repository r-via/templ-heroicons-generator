# templ_heroicons_generator/core/icons.py

import re
import xml.etree.ElementTree as ET
from typing import List, Dict, Optional, Tuple, Any

class Icon:
    """
    Represents a Heroicon to be processed and generated as a Templ component.

    Attributes:
        component_name: The Go-compatible component name (e.g., "Outline_Bars_3").
        file_name: The original SVG file name (e.g., "bars-3").
        style: The icon style ("outline" or "solid").
        elements: A list of dictionaries, where each dictionary represents
                  an SVG graphical element (like 'path', 'circle') and its attributes.
                  Example: [{'tag': 'path', 'attrs': {'d': 'M...', 'stroke': ...}}]
    """
    def __init__(self, component_name: str, file_name: str, style: str):
        """
        Initializes an Icon instance.

        Args:
            component_name: The Go-compatible component name.
            file_name: The original SVG file name.
            style: The icon style ("outline" or "solid").
        """
        self.component_name: str = component_name
        self.file_name: str = file_name
        self.style: str = style
        self.elements: List[Dict[str, Any]] = []

    def __repr__(self) -> str:
        """Provides a developer-friendly string representation of the Icon."""
        return f"Icon(component_name='{self.component_name}', style='{self.style}', file_name='{self.file_name}')"


def _to_svg_file_name(component_part: str) -> str:
    """
    Converts a Go component name part (underscores) to an SVG file name part (hyphens).
    Example: "bars_3" -> "bars-3"

    Args:
        component_part: The part of the component name representing the icon's base name.

    Returns:
        The hyphenated string suitable for an SVG file name.
    """
    return component_part.replace('_', '-')

def _capitalize_first_part(name_with_underscores: str) -> str:
    """
    Capitalizes the first part of an underscore-separated string if it's a known style.
    Ensures consistent Go component naming like 'Outline_Some_Icon' or 'Solid_Another_Icon'.
    If the first part isn't 'outline' or 'solid' (case-insensitive), it capitalizes it
    generically.

    Args:
        name_with_underscores: The input string (e.g., "outline_bars_3").

    Returns:
        The string with its first part (style) correctly capitalized (e.g., "Outline_bars_3").
    """
    if not name_with_underscores:
        return ""
    parts = name_with_underscores.split('_', 1)
    if parts:
        first_part = parts[0]
        # Standardize style capitalization
        if first_part.lower() == "outline":
            capitalized_first = "Outline"
        elif first_part.lower() == "solid":
            capitalized_first = "Solid"
        else:
            # Generic capitalization if not a recognized style (fallback, though unlikely for Heroicons)
            capitalized_first = first_part.capitalize()

        if len(parts) > 1:
            # Capitalize subsequent parts for Go export compatibility if needed
            # For Heroicons, the structure is usually Style_IconName, where IconName can have underscores
            # which we want to preserve but ensure each sub-part of IconName is capitalized.
            # e.g. "bars_3_bottom_left" becomes "Bars_3_Bottom_Left"
            # The raw input from regex is like "Outline_bars_3_bottom_left"
            # We want "Outline_Bars_3_Bottom_Left"
            icon_name_parts = parts[1].split('_')
            capitalized_icon_name_parts = [p.capitalize() for p in icon_name_parts]
            return f"{capitalized_first}_{'_'.join(capitalized_icon_name_parts)}"
        return capitalized_first # Only style part, e.g. if input was just "outline"
    return name_with_underscores


def extract_icon_details(raw_component_name: str) -> Optional[Tuple[str, str, str]]:
    """
    Extracts SVG file name, style, and a normalized Go component name from a raw component name.

    The raw component name is expected to be in the format "Style_icon_name_parts"
    (e.g., "Outline_bars_3" or "solid_check_circle"). The style part can be
    lowercase or capitalized. Icon name parts are converted to lowercase for the SVG
    file name and capitalized for the Go component name.

    Args:
        raw_component_name: The name as found in Templ files (e.g., "@heroicons.Outline_bars_3").

    Returns:
        A tuple (svg_file_name, style, go_component_name) if parsing is successful.
        Example: for "outline_Information_Circle", returns
        ("information-circle", "outline", "Outline_Information_Circle").
        Returns None if the name format is invalid.
    """
    original_parts = raw_component_name.split('_', 1)
    if len(original_parts) != 2:
        return None # Invalid format, needs at least Style_IconName

    style_part, icon_name_part = original_parts
    lower_style = style_part.lower()

    if lower_style not in ["outline", "solid"]:
        return None # Style must be 'outline' or 'solid'
    if not icon_name_part:
        return None # Icon name part cannot be empty

    # Convert icon name part to lowercase for SVG file name, then hyphenate
    # e.g., "Information_Circle" -> "information-circle"
    svg_file_name = _to_svg_file_name(icon_name_part).lower()

    # Generate the Go component name with proper capitalization
    # e.g., "outline_Information_Circle" -> "Outline_Information_Circle"
    # The _capitalize_first_part function now handles more robust capitalization.
    # We pass the original raw_component_name so it can correctly capitalize the style
    # and the subsequent icon name parts.
    go_component_name = _capitalize_first_part(raw_component_name)


    return svg_file_name, lower_style, go_component_name


def extract_svg_elements(svg_content: str) -> List[Dict[str, Any]]:
    """
    Extracts relevant graphical SVG elements from SVG string content.

    Supported elements include <path>, <circle>, <rect>, <ellipse>, <line>,
    <polyline>, <polygon>, and <g>. For <g> elements, their children are
    processed recursively. Attributes on <g> elements themselves (like transforms)
    are not preserved as a distinct group in the output list; their graphical
    children are added directly.

    Args:
        svg_content: A string containing the SVG XML data.

    Returns:
        A list of dictionaries, where each dictionary represents a graphical
        SVG element with its 'tag' and 'attrs'. Returns an empty list if
        parsing fails or no relevant elements are found.
    """
    try:
        # Remove XML declaration and comments to prevent parsing issues with some SVGs
        svg_content_cleaned = re.sub(r'<\?xml[^>]*\?>', '', svg_content, flags=re.IGNORECASE).strip()
        svg_content_cleaned = re.sub(r'<!--.*?-->', '', svg_content_cleaned, flags=re.DOTALL).strip()

        # Ensure there's content left to parse
        if not svg_content_cleaned:
            return []

        root = ET.fromstring(svg_content_cleaned)
        extracted_elements: List[Dict[str, Any]] = []
        # Common graphical SVG elements. Add more if Heroicons starts using others.
        supported_tags = {'path', 'circle', 'rect', 'ellipse', 'line', 'polyline', 'polygon', 'g'}

        # Recursively process elements
        def process_element(element: ET.Element):
            # Extract tag name without namespace (e.g., '{http://www.w3.org/2000/svg}path' -> 'path')
            tag_name = element.tag.split('}')[-1] if '}' in element.tag else element.tag

            if tag_name in supported_tags:
                # Filter out xmlns attributes from element attributes
                attributes = {k: v for k, v in element.attrib.items() if 'xmlns' not in k.lower()}

                if tag_name == 'g':
                    # If it's a group, process its children
                    for child in element:
                        process_element(child)
                else:
                    # For other supported graphical elements, add them
                    extracted_elements.append({'tag': tag_name, 'attrs': attributes})

        # Start processing from the children of the root <svg> element
        for child_element in root:
            process_element(child_element)

        return extracted_elements
    except ET.ParseError:
        # This error will be caught by the caller (downloader.py) which can log it if verbose.
        # Returning an empty list signals failure to parse this SVG.
        return []
    except Exception:
        # Catch any other unexpected errors during SVG processing.
        return []