"""XML schema definitions for Gemini and Claude outputs"""

# Schema version
SCHEMA_VERSION = "2.0.0"

# Schema for sandbox configuration
SANDBOX_CONFIG_SCHEMA = b'''<?xml version="1.0" encoding="UTF-8"?>
<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">
    <xs:element name="sandbox_config">
        <xs:complexType>
            <xs:sequence>
                <xs:element name="template" type="xs:string"/>
                <xs:element name="timeout_ms" type="xs:integer"/>
                <xs:element name="memory_mb" type="xs:integer"/>
                <xs:element name="dependencies" minOccurs="0">
                    <xs:complexType>
                        <xs:sequence>
                            <xs:element name="package" type="xs:string" minOccurs="0" maxOccurs="unbounded"/>
                        </xs:sequence>
                    </xs:complexType>
                </xs:element>
            </xs:sequence>
            <xs:attribute name="version" type="xs:string" use="required"/>
        </xs:complexType>
    </xs:element>
</xs:schema>'''

# Schema for Gemini reasoning output
GEMINI_REASONING_SCHEMA = b'''<?xml version="1.0" encoding="UTF-8"?>
<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">
    <xs:element name="reasoning">
        <xs:complexType>
            <xs:sequence>
                <xs:element name="technical_requirements">
                    <xs:complexType>
                        <xs:sequence>
                            <xs:element name="item" type="xs:string" minOccurs="1" maxOccurs="unbounded"/>
                        </xs:sequence>
                    </xs:complexType>
                </xs:element>
                <xs:element name="implementation_strategy">
                    <xs:complexType>
                        <xs:sequence>
                            <xs:element name="item" type="xs:string" minOccurs="1" maxOccurs="unbounded"/>
                        </xs:sequence>
                    </xs:complexType>
                </xs:element>
                <xs:element name="guidance_for_claude">
                    <xs:complexType>
                        <xs:sequence>
                            <xs:element name="item" type="xs:string" minOccurs="1" maxOccurs="unbounded"/>
                        </xs:sequence>
                    </xs:complexType>
                </xs:element>
                <xs:element name="sandbox_requirements" minOccurs="0">
                    <xs:complexType>
                        <xs:sequence>
                            <xs:element name="template" type="xs:string" minOccurs="0"/>
                            <xs:element name="dependencies" minOccurs="0">
                                <xs:complexType>
                                    <xs:sequence>
                                        <xs:element name="package" type="xs:string" minOccurs="0" maxOccurs="unbounded"/>
                                    </xs:sequence>
                                </xs:complexType>
                            </xs:element>
                        </xs:sequence>
                    </xs:complexType>
                </xs:element>
                <xs:element name="metadata" minOccurs="0">
                    <xs:complexType>
                        <xs:sequence>
                            <xs:element name="item" minOccurs="0" maxOccurs="unbounded">
                                <xs:complexType>
                                    <xs:simpleContent>
                                        <xs:extension base="xs:string">
                                            <xs:attribute name="key" type="xs:string" use="required"/>
                                        </xs:extension>
                                    </xs:simpleContent>
                                </xs:complexType>
                            </xs:element>
                        </xs:sequence>
                    </xs:complexType>
                </xs:element>
            </xs:sequence>
            <xs:attribute name="version" type="xs:string" use="required"/>
        </xs:complexType>
    </xs:element>
</xs:schema>'''

# Schema for Claude synthesis output
CLAUDE_SYNTHESIS_SCHEMA = b'''<?xml version="1.0" encoding="UTF-8"?>
<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">
    <xs:element name="synthesis">
        <xs:complexType>
            <xs:sequence>
                <xs:element name="code_completion" type="xs:string"/>
                <xs:element name="explanation" type="xs:string" minOccurs="0"/>
                <xs:element name="sandbox_config" minOccurs="0">
                    <xs:complexType>
                        <xs:sequence>
                            <xs:element name="template" type="xs:string" minOccurs="0"/>
                            <xs:element name="timeout_ms" type="xs:integer" minOccurs="0"/>
                            <xs:element name="memory_mb" type="xs:integer" minOccurs="0"/>
                            <xs:element name="dependencies" minOccurs="0">
                                <xs:complexType>
                                    <xs:sequence>
                                        <xs:element name="package" type="xs:string" minOccurs="0" maxOccurs="unbounded"/>
                                    </xs:sequence>
                                </xs:complexType>
                            </xs:element>
                        </xs:sequence>
                    </xs:complexType>
                </xs:element>
                <xs:element name="metadata" minOccurs="0">
                    <xs:complexType>
                        <xs:sequence>
                            <xs:element name="item" minOccurs="0" maxOccurs="unbounded">
                                <xs:complexType>
                                    <xs:simpleContent>
                                        <xs:extension base="xs:string">
                                            <xs:attribute name="key" type="xs:string" use="required"/>
                                        </xs:extension>
                                    </xs:simpleContent>
                                </xs:complexType>
                            </xs:element>
                        </xs:sequence>
                    </xs:complexType>
                </xs:element>
            </xs:sequence>
            <xs:attribute name="version" type="xs:string" use="required"/>
        </xs:complexType>
    </xs:element>
</xs:schema>'''

# Fallback template for Gemini when parsing fails
GEMINI_FALLBACK_TEMPLATE = '''<?xml version="1.0" encoding="UTF-8"?>
<reasoning version="{version}">
    <technical_requirements>
        <item>Unable to parse Gemini output - using fallback template</item>
    </technical_requirements>
    <implementation_strategy>
        <item>Proceed with basic implementation</item>
    </implementation_strategy>
    <guidance_for_claude>
        <item>Generate minimal working code</item>
    </guidance_for_claude>
    <metadata>
        <item key="fallback">true</item>
        <item key="timestamp">TIMESTAMP_PLACEHOLDER</item>
    </metadata>
</reasoning>'''

# Fallback template for Claude when parsing fails
CLAUDE_FALLBACK_TEMPLATE = '''<?xml version="1.0" encoding="UTF-8"?>
<synthesis version="{version}">
    <code_completion>// Failed to parse Claude output
// Using fallback template
console.error("Code generation failed");</code_completion>
    <explanation>Code generation failed - using fallback template</explanation>
    <metadata>
        <item key="fallback">true</item>
        <item key="timestamp">TIMESTAMP_PLACEHOLDER</item>
    </metadata>
</synthesis>'''

def get_fallback_template(template_type: str) -> str:
    """Get a fallback template with current version"""
    if template_type.lower() == 'gemini':
        return GEMINI_FALLBACK_TEMPLATE.format(version=SCHEMA_VERSION)
    elif template_type.lower() == 'claude':
        return CLAUDE_FALLBACK_TEMPLATE.format(version=SCHEMA_VERSION)
    else:
        raise ValueError(f"Unknown template type: {template_type}") 