# templ_heroicons_generator/core/icons.py

import re
import xml.etree.ElementTree as ET
from typing import List, Dict, Optional, Tuple, Any

class Icon:
    """
    Represents a Heroicon to be processed and generated as a Templ component.

    Attributes:
        component_name: The Go-compatible component name (e.g., "Outline_bars_3").
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
    Capitalizes the first part of an underscore-separated string.
    Example: "outline_bars_3" -> "Outline_bars_3"

    Args:
        name_with_underscores: The input string.

    Returns:
        The string with its first part capitalized.
    """
    if not name_with_underscores:
        return ""
    parts = name_with_underscores.split('_', 1)
    if parts:
        capitalized_first = parts[0].capitalize()
        if len(parts) > 1:
            return f"{capitalized_first}_{parts[1]}"
        return capitalized_first
    return name_with_underscores


def extract_icon_details(raw_component_name: str) -> Optional[Tuple[str, str, str]]:
    """
    Extracts SVG file name, style, and a normalized Go component name from a raw component name.

    The raw component name is expected to be in the format "Style_icon_name_parts"
    (e.g., "Outline_bars_3" or "solid_check_circle"). The style part can be
    lowercase or capitalized.

    Args:
        raw_component_name: The name as found in Templ files (e.g., "@heroicons.Outline_bars_3").

    Returns:
        A tuple (svg_file_name, style, go_component_name) if parsing is successful.
        Example: for "outline_bars_3", returns ("bars-3", "outline", "Outline_bars_3").
        Returns None if the name format is invalid.
    """
    original_parts = raw_component_name.split('_', 1)
    if len(original_parts) != 2:
        return None

    style_part, icon_name_part = original_parts
    lower_style = style_part.lower()

    if lower_style not in ["outline", "solid"]:
        return None
    if not icon_name_part:
        return None

    svg_file_name = _to_svg_file_name(icon_name_part)
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
        svg_content_cleaned = re.sub(r'<\?xml[^>]*\?>', '', svg_content, flags=re.IGNORECASE).strip()
        svg_content_cleaned = re.sub(r'<!--.*?-->', '', svg_content_cleaned, flags=re.DOTALL).strip()

        root = ET.fromstring(svg_content_cleaned)
        extracted_elements: List[Dict[str, Any]] = []
        supported_tags = {'path', 'circle', 'rect', 'ellipse', 'line', 'polyline', 'polygon', 'g'}

        def process_element(element: ET.Element):
            tag_name = element.tag.split('}')[-1]

            if tag_name in supported_tags:
                attributes = {k: v for k, v in element.attrib.items() if 'xmlns' not in k.lower()}
                if tag_name == 'g':
                    for child in element:
                        process_element(child)
                else:
                    extracted_elements.append({'tag': tag_name, 'attrs': attributes})

        for child_element in root:
            process_element(child_element)

        return extracted_elements
    except ET.ParseError: # Raised for XML parsing errors
        # The caller (downloader.py) should log this error if verbose.
        # Returning an empty list signals failure.
        pass
    except Exception: # Catch any other unexpected errors during SVG processing
        # The caller (downloader.py) should log this error if verbose.
        pass
    return []