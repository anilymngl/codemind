import logging
from typing import Dict, Any, Optional, List
import xml.etree.ElementTree as ET
from lxml import etree
from io import StringIO, BytesIO
from datetime import datetime

from models.xml_schemas import (
    CLAUDE_SYNTHESIS_SCHEMA,
    SCHEMA_VERSION,
    get_fallback_template
)
from mvp_orchestrator.error_types import XMLProcessingError
from mvp_orchestrator.secure_sandbox import SandboxConfig

logger = logging.getLogger(__name__)

class ClaudeXMLValidator:
    """Validates and processes XML output from Claude"""
    
    def __init__(self):
        """Initialize the XML validator with schema"""
        try:
            parser = etree.XMLParser(remove_blank_text=True)
            
            # Handle schema content based on type
            logger.debug(f"Processing schema of type: {type(CLAUDE_SYNTHESIS_SCHEMA)}")
            if isinstance(CLAUDE_SYNTHESIS_SCHEMA, bytes):
                logger.debug("Processing bytes schema...")
                schema_doc = etree.parse(BytesIO(CLAUDE_SYNTHESIS_SCHEMA), parser)
            else:
                logger.debug("Processing string schema...")
                # Remove any encoding declaration if present in string
                schema_str = CLAUDE_SYNTHESIS_SCHEMA
                if '<?xml' in schema_str:
                    logger.debug("Removing XML encoding declaration...")
                    schema_str = '\n'.join(
                        line for line in schema_str.split('\n')
                        if not line.strip().startswith('<?xml')
                    )
                schema_doc = etree.parse(StringIO(schema_str), parser)
            
            self.schema = etree.XMLSchema(schema_doc)
            self.parser = parser
            logger.info(f"Initialized XML validator with schema version {SCHEMA_VERSION}")
        except Exception as e:
            logger.error(f"Failed to initialize XML schema: {e}")
            raise XMLProcessingError("Failed to initialize XML schema", details={'error': str(e)})
            
    def validate_and_process(self, xml_content: str) -> Dict[str, Any]:
        """Validate and process XML content"""
        if not xml_content:
            logger.error("Empty XML content received")
            raise XMLProcessingError("Failed to process empty XML content")
        
        try:
            # Log initial content
            logger.debug("Starting XML validation", extra={
                'content_length': len(xml_content),
                'content_preview': xml_content[:200],
                'has_xml_decl': '<?xml' in xml_content
            })
            
            # Clean up XML content
            xml_content = xml_content.strip()
            logger.debug("Cleaned whitespace", extra={
                'new_length': len(xml_content)
            })
            
            # Remove markdown code block markers if present
            if xml_content.startswith("```xml"):
                xml_content = xml_content.replace("```xml", "", 1).strip()
            if xml_content.endswith("```"):
                xml_content = xml_content.rsplit("```", 1)[0].strip()
            logger.debug("Cleaned markdown markers", extra={
                'new_length': len(xml_content),
                'content_start': xml_content[:100]
            })
            
            # Remove XML declaration if present
            if xml_content.startswith('<?xml'):
                logger.debug("Found XML declaration", extra={
                    'declaration': xml_content[0:xml_content.find('?>') + 2]
                })
                xml_content = xml_content[xml_content.find('?>') + 2:].lstrip()
                logger.debug("Removed XML declaration", extra={
                    'new_length': len(xml_content),
                    'content_start': xml_content[:100]
                })
            
            # Ensure content starts with synthesis tag
            if not xml_content.lstrip().startswith('<synthesis'):
                logger.debug("Adding synthesis root element")
                xml_content = f"<synthesis version=\"2.0.0\">{xml_content}</synthesis>"
            
            # Convert to bytes with explicit encoding
            logger.debug("Converting to UTF-8 bytes")
            xml_bytes = xml_content.encode('utf-8')
            logger.debug("Converted to bytes", extra={
                'bytes_length': len(xml_bytes)
            })
            
            # Parse XML using bytes
            logger.debug("Parsing XML bytes")
            try:
                # First try with lenient parser
                parser = etree.XMLParser(
                    remove_blank_text=True,
                    recover=True,  # Try to recover from errors
                    remove_comments=True,
                    resolve_entities=False
                )
                xml_doc = etree.fromstring(xml_bytes, parser=parser)
                logger.debug("Successfully parsed XML with recovery", extra={
                    'root_tag': xml_doc.tag,
                    'num_children': len(xml_doc)
                })
            except Exception as parse_error:
                logger.warning("Lenient parsing failed, attempting cleanup", extra={
                    'error': str(parse_error)
                })
                # Try cleaning problematic characters
                xml_content = self._clean_xml_content(xml_content)
                xml_bytes = xml_content.encode('utf-8')
                xml_doc = etree.fromstring(xml_bytes, parser=parser)
                logger.debug("Successfully parsed XML after cleanup")
            
            # Extract components
            logger.debug("Extracting XML components")
            result = {
                'code_completion': self._get_element_text(xml_doc, './/code_completion'),
                'explanation': self._get_element_text(xml_doc, './/explanation'),
                'metadata': self._get_metadata(xml_doc)
            }
            
            logger.debug("Extracted components", extra={
                'has_code': bool(result['code_completion']),
                'has_explanation': bool(result['explanation']),
                'num_metadata': len(result['metadata'])
            })
            
            # Validate required fields
            if not result['code_completion']:
                logger.error("Missing required code_completion element")
                raise XMLProcessingError("Missing code completion")
            
            logger.info("Successfully processed XML", extra={
                'result_keys': list(result.keys())
            })
            return result
        
        except etree.XMLSyntaxError as e:
            logger.error("XML syntax error", extra={
                'error': str(e),
                'line': getattr(e, 'lineno', None),
                'column': getattr(e, 'offset', None),
                'content_preview': xml_content[:500] if 'xml_content' in locals() else None
            })
            raise XMLProcessingError("Failed to parse XML", details={
                'error': str(e),
                'line': getattr(e, 'lineno', None),
                'column': getattr(e, 'offset', None)
            })
        
        except Exception as e:
            logger.error("Failed to process XML", exc_info=True, extra={
                'error_type': type(e).__name__,
                'error_msg': str(e),
                'content_length': len(xml_content) if 'xml_content' in locals() else None
            })
            raise XMLProcessingError("Failed to process XML", details={'error': str(e)})
            
    def _process_valid_xml(self, xml_doc: etree._Element) -> Dict[str, Any]:
        """Process valid XML document"""
        try:
            root = xml_doc.getroot()
            
            # Extract sections
            result = {
                'code_completion': '',
                'explanation': None,
                'sandbox_config': None,
                'metadata': {}
            }
            
            # Extract code completion
            code_elem = root.find('code_completion')
            if code_elem is not None and code_elem.text:
                result['code_completion'] = code_elem.text.strip()
            else:
                raise XMLProcessingError("Missing required code_completion element")
                
            # Extract optional explanation
            explanation_elem = root.find('explanation')
            if explanation_elem is not None and explanation_elem.text:
                result['explanation'] = explanation_elem.text.strip()
                
            # Extract sandbox configuration if present
            sandbox_elem = root.find('sandbox_config')
            if sandbox_elem is not None:
                result['sandbox_config'] = self._extract_sandbox_config(sandbox_elem)
                
            # Process metadata if present
            metadata_elem = root.find('metadata')
            if metadata_elem is not None:
                result['metadata'] = self._extract_metadata(metadata_elem)
                
            return result
            
        except Exception as e:
            logger.error(f"Error processing valid XML: {e}")
            raise XMLProcessingError("Error processing valid XML", details={'error': str(e)})
            
    def _process_with_recovery(self, xml_content: str) -> Dict[str, Any]:
        """Attempt to recover and process invalid XML"""
        logger.info("Attempting XML recovery")
        
        try:
            # First try to extract content using basic string operations
            recovered_content = self._basic_string_recovery(xml_content)
            if recovered_content:
                logger.info("Basic string recovery successful")
                return recovered_content
        except Exception as e:
            logger.warning(f"Basic string recovery failed: {e}")
            
        # If basic recovery fails, use fallback template
        logger.info("Using fallback template")
        return self._process_fallback()
        
    def _basic_string_recovery(self, xml_content: str) -> Optional[Dict[str, Any]]:
        """Attempt to recover content using basic string operations"""
        result = {
            'code_completion': '',
            'explanation': None,
            'sandbox_config': None,
            'metadata': {}
        }
        
        # Try to extract code completion
        try:
            start_tag = "<code_completion>"
            end_tag = "</code_completion>"
            start_idx = xml_content.find(start_tag)
            end_idx = xml_content.find(end_tag)
            
            if start_idx != -1 and end_idx != -1:
                code = xml_content[start_idx + len(start_tag):end_idx].strip()
                if code:
                    result['code_completion'] = code
                    
            # Try to extract explanation if present
            start_tag = "<explanation>"
            end_tag = "</explanation>"
            start_idx = xml_content.find(start_tag)
            end_idx = xml_content.find(end_tag)
            
            if start_idx != -1 and end_idx != -1:
                explanation = xml_content[start_idx + len(start_tag):end_idx].strip()
                if explanation:
                    result['explanation'] = explanation
                    
            # Try to extract sandbox config if present
            if "<sandbox_config>" in xml_content and "</sandbox_config>" in xml_content:
                try:
                    sandbox_xml = xml_content[
                        xml_content.find("<sandbox_config>"):
                        xml_content.find("</sandbox_config>") + len("</sandbox_config>")
                    ]
                    sandbox_doc = etree.fromstring(sandbox_xml)
                    result['sandbox_config'] = self._extract_sandbox_config(sandbox_doc)
                except Exception as e:
                    logger.warning(f"Failed to extract sandbox config: {e}")
                    
        except Exception as e:
            logger.warning(f"Failed to extract content: {e}")
            
        # Return recovered content only if we found code completion
        return result if result['code_completion'] else None
        
    def _process_fallback(self) -> Dict[str, Any]:
        """Process using fallback template"""
        try:
            fallback_content = get_fallback_template('claude').format(
                timestamp=datetime.utcnow().isoformat()
            )
            xml_doc = etree.parse(StringIO(fallback_content), self.parser)
            return self._process_valid_xml(xml_doc)
        except Exception as e:
            logger.error(f"Error processing fallback template: {e}")
            return {
                'code_completion': '// Failed to process Claude output\n// Please try again',
                'explanation': None,
                'sandbox_config': None,
                'metadata': {'error': str(e)}
            }
            
    def _extract_metadata(self, metadata_elem: etree._Element) -> Dict[str, Any]:
        """Extract metadata from XML element"""
        metadata = {}
        for item in metadata_elem.findall('item'):
            key = item.get('key')
            if key and item.text:
                metadata[key] = item.text.strip()
        return metadata
        
    def _extract_sandbox_config(self, sandbox_elem: etree._Element) -> Dict[str, Any]:
        """Extract sandbox configuration from XML element"""
        config = {}
        
        # Extract template
        template_elem = sandbox_elem.find('template')
        if template_elem is not None and template_elem.text:
            config['template'] = template_elem.text.strip()
            
        # Extract timeout
        timeout_elem = sandbox_elem.find('timeout_ms')
        if timeout_elem is not None and timeout_elem.text:
            try:
                config['timeout_ms'] = int(timeout_elem.text)
            except ValueError:
                logger.warning(f"Invalid timeout value: {timeout_elem.text}")
                
        # Extract memory limit
        memory_elem = sandbox_elem.find('memory_mb')
        if memory_elem is not None and memory_elem.text:
            try:
                config['memory_mb'] = int(memory_elem.text)
            except ValueError:
                logger.warning(f"Invalid memory value: {memory_elem.text}")
                
        # Extract dependencies
        deps_elem = sandbox_elem.find('dependencies')
        if deps_elem is not None:
            packages = []
            for pkg_elem in deps_elem.findall('package'):
                if pkg_elem.text:
                    packages.append(pkg_elem.text.strip())
            if packages:
                config['dependencies'] = packages
                
        return config 

    def _clean_xml_content(self, content: str) -> str:
        """Clean problematic characters from XML content"""
        # Remove any control characters except whitespace
        content = ''.join(char for char in content if char >= ' ' or char in '\n\r\t')
        
        # Fix common XML issues
        replacements = {
            '&': '&amp;',  # Escape ampersands
            '<br>': '\n',  # Convert HTML breaks to newlines
            '</br>': '',
            '...': '…',    # Replace ellipsis with single character
        }
        
        for old, new in replacements.items():
            content = content.replace(old, new)
        
        # Remove any double angle brackets
        content = content.replace('<<', '<').replace('>>', '>')
        
        return content

    def _get_element_text(self, xml_doc: etree._Element, xpath: str) -> Optional[str]:
        """Get text content of an element by XPath"""
        try:
            elements = xml_doc.xpath(xpath)
            logger.debug(f"XPath search for {xpath}", extra={
                'found_elements': len(elements),
                'has_text': bool(elements and elements[0] is not None and elements[0].text)
            })
            if elements and elements[0] is not None and elements[0].text:
                return elements[0].text.strip()
            return None
        except Exception as e:
            logger.error(f"Error getting element text for {xpath}", exc_info=True)
            return None

    def _get_metadata(self, xml_doc: etree._Element) -> Dict[str, Any]:
        """Extract metadata from XML document"""
        try:
            metadata = {}
            items = xml_doc.xpath('.//metadata/item')
            logger.debug("Extracting metadata", extra={
                'num_items': len(items)
            })
            for item in items:
                key = item.get('key')
                if key and item.text:
                    metadata[key] = item.text.strip()
                    logger.debug(f"Added metadata item", extra={
                        'key': key,
                        'value_length': len(item.text.strip())
                    })
            return metadata
        except Exception as e:
            logger.error("Error extracting metadata", exc_info=True)
            return {}