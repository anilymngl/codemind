"""XML processor for Gemini responses"""
import logging
from typing import Dict, Any, Optional
from io import StringIO, BytesIO
from lxml import etree
from datetime import datetime
import time
from logger import log_info, log_debug, log_error, log_warning, log_performance

from models.xml_schemas import (
    GEMINI_REASONING_SCHEMA,
    SCHEMA_VERSION,
    get_fallback_template
)
from mvp_orchestrator.error_types import XMLProcessingError

logger = logging.getLogger(__name__)

class GeminiXMLProcessor:
    """Processor for Gemini XML responses"""
    
    def __init__(self):
        """Initialize XML processor with schema"""
        logger.info("Initializing GeminiXMLProcessor...")
        try:
            # Create parser with settings
            logger.debug("Creating XML parser...")
            self.parser = etree.XMLParser(remove_blank_text=True)
            
            # Handle schema content based on type
            logger.debug(f"Processing schema of type: {type(GEMINI_REASONING_SCHEMA)}")
            if isinstance(GEMINI_REASONING_SCHEMA, bytes):
                logger.debug("Processing bytes schema...")
                schema_doc = etree.parse(BytesIO(GEMINI_REASONING_SCHEMA), self.parser)
            else:
                logger.debug("Processing string schema...")
                # Remove any encoding declaration if present in string
                schema_str = GEMINI_REASONING_SCHEMA
                if '<?xml' in schema_str:
                    logger.debug("Removing XML encoding declaration...")
                    schema_str = '\n'.join(
                        line for line in schema_str.split('\n')
                        if not line.strip().startswith('<?xml')
                    )
                schema_doc = etree.parse(StringIO(schema_str), self.parser)
            
            logger.debug("Creating XML schema...")
            self.schema = etree.XMLSchema(schema_doc)
            logger.info(f"Successfully initialized XML processor with schema version {SCHEMA_VERSION}")
            
        except Exception as e:
            logger.error(f"Failed to initialize XML schema: {e}", exc_info=True)
            raise XMLProcessingError("Failed to initialize XML schema", details={'error': str(e)})
            
    def validate_and_process(
        self,
        xml_content: str,
        allow_recovery: bool = True
    ) -> Dict[str, Any]:
        """
        Validate and process XML content from Gemini
        
        Args:
            xml_content: The XML string to process
            allow_recovery: Whether to attempt recovery for invalid XML
            
        Returns:
            Dictionary containing processed content
            
        Raises:
            XMLProcessingError: If validation fails and recovery is not allowed or fails
        """
        start_time = time.time()
        log_info("Starting XML validation and processing", extra={
            'content_length': len(xml_content),
            'allow_recovery': allow_recovery
        })
        
        try:
            # Clean up XML content
            xml_content = xml_content.strip()
            log_debug("Initial content", extra={
                'content_preview': xml_content[:200],
                'length': len(xml_content)
            })
            
            # Clean markdown code block if present
            if xml_content.startswith("```xml"):
                xml_content = xml_content.replace("```xml", "", 1).strip()
            if xml_content.endswith("```"):
                xml_content = xml_content.rsplit("```", 1)[0].strip()
            log_debug("Cleaned markdown markers", extra={
                'new_length': len(xml_content)
            })
            
            # Remove XML declaration if present
            if xml_content.startswith("<?xml"):
                xml_content = xml_content[xml_content.find("?>") + 2:].lstrip()
                log_debug("Removed XML declaration", extra={
                    'new_length': len(xml_content)
                })
            
            # Ensure content starts with reasoning tag
            if not xml_content.lstrip().startswith('<reasoning'):
                log_debug("Adding reasoning root element")
                xml_content = f"<reasoning version=\"2.0.0\">{xml_content}</reasoning>"
            
            # Clean problematic characters
            xml_content = self._clean_xml_content(xml_content)
            log_debug("Cleaned problematic characters", extra={
                'new_length': len(xml_content)
            })
            
            # Parse XML with recovery options
            log_debug("Parsing XML with recovery options...")
            parser = etree.XMLParser(
                remove_blank_text=True,
                recover=True,
                remove_comments=True,
                resolve_entities=False,
                huge_tree=True
            )
            
            try:
                xml_doc = etree.parse(StringIO(xml_content), parser)
                log_debug("Successfully parsed XML")
            except Exception as parse_error:
                log_warning("Initial parsing failed, attempting cleanup", extra={
                    'error': str(parse_error)
                })
                # Try more aggressive cleaning
                xml_content = self._aggressive_clean(xml_content)
                xml_doc = etree.parse(StringIO(xml_content), parser)
                log_debug("Successfully parsed XML after aggressive cleanup")
            
            # Extract components
            log_debug("Extracting components...")
            result = {
                'technical_requirements': [],
                'implementation_strategy': [],
                'guidance_for_claude': [],
                'sandbox_requirements': None,
                'metadata': {},
                'thoughts': []
            }
            
            # Extract each section with error handling
            root = xml_doc.getroot()
            
            # Technical Requirements
            for req in root.findall('.//technical_requirements/item'):
                if req.text and req.text.strip():
                    result['technical_requirements'].append(req.text.strip())
            
            # Implementation Strategy
            for step in root.findall('.//implementation_strategy/item'):
                if step.text and step.text.strip():
                    result['implementation_strategy'].append(step.text.strip())
            
            # Guidance for Claude
            for guide in root.findall('.//guidance_for_claude/item'):
                if guide.text and guide.text.strip():
                    result['guidance_for_claude'].append(guide.text.strip())
            
            # Sandbox Requirements
            sandbox_elem = root.find('.//sandbox_requirements')
            if sandbox_elem is not None:
                result['sandbox_requirements'] = self._extract_sandbox_config(sandbox_elem)
            
            # Metadata
            metadata_elem = root.find('.//metadata')
            if metadata_elem is not None:
                result['metadata'] = self._extract_metadata(metadata_elem)
            
            # Validate minimum requirements
            if not result['technical_requirements'] and not result['implementation_strategy']:
                log_warning("Missing required sections")
                if allow_recovery:
                    log_info("Attempting recovery for missing sections")
                    return self._process_with_recovery(xml_content)
                raise XMLProcessingError("Missing required sections")
            
            duration_ms = (time.time() - start_time) * 1000
            log_performance("xml_processing", duration_ms, {
                'success': True,
                'num_requirements': len(result['technical_requirements']),
                'num_strategy': len(result['implementation_strategy'])
            })
            
            return result
            
        except etree.XMLSyntaxError as e:
            log_error("XML syntax error", extra={
                'error': str(e),
                'line': getattr(e, 'lineno', None),
                'column': getattr(e, 'offset', None)
            })
            if allow_recovery:
                log_info("Attempting recovery for syntax error")
                return self._process_with_recovery(xml_content)
            raise XMLProcessingError("Failed to parse XML", details={
                'error': str(e),
                'line': getattr(e, 'lineno', None),
                'column': getattr(e, 'offset', None)
            })
            
        except Exception as e:
            log_error("Failed to process XML", exc_info=True)
            if allow_recovery:
                log_info("Attempting recovery for processing error")
                return self._process_with_recovery(xml_content)
            raise XMLProcessingError("Failed to process XML", details={'error': str(e)})

    def _aggressive_clean(self, content: str) -> str:
        """Aggressively clean problematic XML content"""
        # Remove any non-printable characters
        content = ''.join(char for char in content if char.isprintable() or char in '\n\r\t')
        
        # Fix common XML issues
        replacements = {
            '&': '&amp;',
            '<br>': '\n',
            '</br>': '',
            '...': '…',
            '<<': '<',
            '>>': '>',
            '--': '—',
            '<p>': '',
            '</p>': '\n',
            '<div>': '',
            '</div>': '\n'
        }
        
        for old, new in replacements.items():
            content = content.replace(old, new)
        
        # Remove any HTML-style comments
        while '<!--' in content and '-->' in content:
            start = content.find('<!--')
            end = content.find('-->') + 3
            content = content[:start] + content[end:]
        
        # Ensure proper XML structure
        if '<reasoning' not in content:
            content = f"<reasoning version=\"2.0.0\">{content}</reasoning>"
        
        return content.strip()

    def _clean_xml_content(self, content: str) -> str:
        """Clean problematic characters from XML content"""
        # Remove control characters
        content = ''.join(char for char in content if char >= ' ' or char in '\n\r\t')
        
        # Fix common XML issues
        replacements = {
            '&': '&amp;',  # Escape ampersands
            '<br>': '\n',  # Convert HTML breaks to newlines
            '</br>': '',
            '...': '…',    # Replace ellipsis with single character
            '<<': '<',     # Fix double angle brackets
            '>>': '>'
        }
        
        for old, new in replacements.items():
            content = content.replace(old, new)
        
        return content.strip()

    def _process_with_recovery(self, xml_content: str) -> Dict[str, Any]:
        """Attempt to recover and process invalid XML"""
        start_time = time.time()
        log_info("Attempting XML recovery...")
        
        try:
            # First try to extract content using basic string operations
            log_debug("Attempting basic string recovery...")
            recovered_content = self._basic_string_recovery(xml_content)
            if recovered_content:
                log_info("Basic string recovery successful", extra={
                    'recovered_sections': list(recovered_content.keys())
                })
                return recovered_content
        except Exception as e:
            log_warning("Basic string recovery failed", extra={'error': str(e)})
            
        # If basic recovery fails, use fallback template
        log_info("Using fallback template...")
        result = self._process_fallback()
        
        duration_ms = (time.time() - start_time) * 1000
        log_performance("xml_recovery", duration_ms, {
            'recovery_method': 'fallback',
            'success': bool(result)
        })
        
        return result
        
    def _basic_string_recovery(self, xml_content: str) -> Optional[Dict[str, Any]]:
        """Attempt to recover content using basic string operations"""
        logger.debug("Starting basic string recovery...")
        result = {
            'technical_requirements': [],
            'implementation_strategy': [],
            'guidance_for_claude': [],
            'sandbox_requirements': None,
            'metadata': {}
        }
        
        try:
            # Try to extract requirements
            logger.debug("Extracting requirements from string...")
            start_tag = "<technical_requirements>"
            end_tag = "</technical_requirements>"
            if start_tag in xml_content and end_tag in xml_content:
                section = xml_content[
                    xml_content.find(start_tag) + len(start_tag):
                    xml_content.find(end_tag)
                ]
                for item in section.split("<item>"):
                    if "</item>" in item:
                        text = item[:item.find("</item>")].strip()
                        if text:
                            result['technical_requirements'].append(text)
                            
            # Try to extract strategy
            logger.debug("Extracting strategy from string...")
            start_tag = "<implementation_strategy>"
            end_tag = "</implementation_strategy>"
            if start_tag in xml_content and end_tag in xml_content:
                section = xml_content[
                    xml_content.find(start_tag) + len(start_tag):
                    xml_content.find(end_tag)
                ]
                for item in section.split("<item>"):
                    if "</item>" in item:
                        text = item[:item.find("</item>")].strip()
                        if text:
                            result['implementation_strategy'].append(text)
                            
            # Try to extract guidance
            logger.debug("Extracting guidance from string...")
            start_tag = "<guidance_for_claude>"
            end_tag = "</guidance_for_claude>"
            if start_tag in xml_content and end_tag in xml_content:
                section = xml_content[
                    xml_content.find(start_tag) + len(start_tag):
                    xml_content.find(end_tag)
                ]
                for item in section.split("<item>"):
                    if "</item>" in item:
                        text = item[:item.find("</item>")].strip()
                        if text:
                            result['guidance_for_claude'].append(text)
                            
            # Try to extract sandbox requirements
            logger.debug("Extracting sandbox requirements from string...")
            if "<sandbox_requirements>" in xml_content and "</sandbox_requirements>" in xml_content:
                try:
                    sandbox_xml = xml_content[
                        xml_content.find("<sandbox_requirements>"):
                        xml_content.find("</sandbox_requirements>") + len("</sandbox_requirements>")
                    ]
                    sandbox_doc = etree.fromstring(sandbox_xml)
                    result['sandbox_requirements'] = self._extract_sandbox_config(sandbox_doc)
                except Exception as e:
                    logger.warning(f"Failed to extract sandbox config: {e}")
                    
        except Exception as e:
            logger.warning(f"Failed to extract content: {e}")
            
        # Return recovered content only if we found something
        has_content = any(result.values())
        logger.info(f"Basic string recovery {'successful' if has_content else 'failed'}")
        return result if has_content else None
        
    def _process_fallback(self) -> Dict[str, Any]:
        """Process using fallback template"""
        logger.info("Using fallback template...")
        try:
            fallback_content = get_fallback_template('gemini').format(
                timestamp=datetime.utcnow().isoformat()
            )
            xml_doc = etree.parse(StringIO(fallback_content), self.parser)
            return self._process_valid_xml(xml_doc)
        except Exception as e:
            logger.error(f"Error processing fallback template: {e}")
            return {
                'technical_requirements': ["Unable to process Gemini output"],
                'implementation_strategy': ["Using fallback implementation"],
                'guidance_for_claude': ["Generate minimal working code"],
                'sandbox_requirements': None,
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
        try:
            config = {}
            
            # Extract template
            template = sandbox_elem.findtext('template')
            if template:
                config['template'] = template.strip()
            
            # Extract dependencies
            deps = sandbox_elem.find('dependencies')
            if deps is not None:
                packages = []
                for pkg in deps.findall('package'):
                    if pkg.text and pkg.text.strip():
                        packages.append(pkg.text.strip())
                if packages:
                    config['dependencies'] = packages
            
            return config
        except Exception as e:
            log_warning(f"Error extracting sandbox config: {e}")
            return {} 