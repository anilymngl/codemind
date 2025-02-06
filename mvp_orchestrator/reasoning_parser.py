from dataclasses import dataclass
from typing import List, Optional
import json
from pydantic import BaseModel, Field
from logger import log_error, log_debug

class StructuredReasoning(BaseModel):
    """Pydantic model for structured reasoning output."""
    requirements: List[str] = Field(..., description="Technical requirements")
    strategy: List[str] = Field(..., description="Implementation strategy")
    guidance: List[str] = Field(..., description="Guidance for Claude")

class ReasoningParser:
    """Parser for structured reasoning output in JSON format."""

    def parse_reasoning(self, json_content: str) -> Optional[StructuredReasoning]:
        """Parse JSON content into StructuredReasoning model."""
        log_debug(f"ReasoningParser.parse_reasoning() - JSON Content:\n{json_content}")
        try:
            # Parse JSON string into dict
            data = json.loads(json_content)
            
            # Convert to Pydantic model for validation
            result = StructuredReasoning(
                requirements=data.get('technical_requirements', []),
                strategy=data.get('implementation_strategy', []),
                guidance=data.get('guidance_for_claude', [])
            )
            
            log_debug(f"Successfully parsed reasoning: {result}")
            return result
            
        except json.JSONDecodeError as e:
            log_error(f"JSON parsing error in ReasoningParser: {e}")
            return None
        except Exception as e:
            log_error(f"Error in ReasoningParser: {e}")
            return None