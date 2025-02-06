from dataclasses import dataclass
from typing import List, Optional
import xml.etree.ElementTree as ET
from logger import log_error, log_debug # Assuming you have a logger module

@dataclass
class StructuredReasoning:
    requirements: List[str]
    strategy: List[str]
    guidance: List[str]

class ReasoningParser:
    """Minimal parser for structured reasoning output."""

    def parse_reasoning(self, xml_content: str) -> Optional[StructuredReasoning]:
        log_debug(f"ReasoningParser.parse_reasoning() - XML Content:\n{xml_content}")
        try:
            root = ET.fromstring(f"<root>{xml_content}</root>") # Wrap in root for robustness
            return StructuredReasoning(
                requirements=self._extract_section(root, 'technical_requirements'),
                strategy=self._extract_section(root, 'implementation_strategy'),
                guidance=self._extract_section(root, 'guidance_for_claude')
            )
        except ET.ParseError as e: # Catch specific XML parsing error
            log_error(f"XML Parsing error in ReasoningParser: {e}")
            return None
        except Exception as e: # Catch other potential errors
            log_error(f"Error in ReasoningParser: {e}")
            return None

    def _extract_section(self, root: ET.Element, section: str) -> List[str]:
        """Extract content from a section, with basic error handling."""
        log_debug(f"ReasoningParser._extract_section() - section: {section}")
        try:
            section_element = root.find(f".//{section}")
            if section_element is not None:
                items = []
                for item_element in section_element.findall(".//item"): # Find all item tags
                    if item_element.text:
                        items.append(item_element.text.strip()) # Extract text and strip whitespace
                log_debug(f"ReasoningParser._extract_section() - extracted items: {items}")
                return items
            else:
                log_debug(f"ReasoningParser._extract_section() - section not found: {section}")
                return [] # Return empty list if section is missing
        except Exception as e: # Catch errors during section extraction
            log_error(f"Error extracting section '{section}': {e}")
            return []