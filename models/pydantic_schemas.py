from pydantic import BaseModel, Field
from typing import Optional, List


class SandboxConfig(BaseModel):
    template: Optional[str] = None
    timeout_ms: Optional[int] = None
    memory_mb: Optional[int] = None
    dependencies: Optional[List[str]] = Field(default_factory=list)


class MetadataItem(BaseModel):
    key: str
    value: str


class ClaudeSynthesisResult(BaseModel):
    code_completion: str = Field(..., description="Generated code snippet")
    explanation: Optional[str] = Field(None, description="Explanation of the code")
    sandbox_config: Optional[SandboxConfig] = None
    metadata: Optional[List[MetadataItem]] = Field(default_factory=list)
    version: str = Field("2.0.0", description="Synthesis version")


class GeminiReasoningResult(BaseModel):
    reasoning_steps: List[str] = Field(..., description="List of reasoning steps")
    conclusion: str = Field(..., description="Final conclusion of reasoning")
    metadata: Optional[List[MetadataItem]] = Field(default_factory=list)
    version: str = Field("2.0.0", description="Reasoning version") 