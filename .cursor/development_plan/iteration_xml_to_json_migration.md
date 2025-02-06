---
description: XML to JSON Migration - Iterative Development Roadmap (5 Iterations)
---

**Guiding Principles for Iteration Design:**

*   **Principle 1: Phased Migration:** Migrate components incrementally, starting with Claude Synthesis, then Gemini Reasoning, Gemini Synthesis (if applicable), Orchestrator, and finally Fallback/Cleanup. This minimizes risk and allows for iterative learning.
*   **Principle 2: JSON First:** Prioritize JSON as the structured output format for all new development and migration efforts.  Deprecate XML usage systematically.
*   **Principle 3: Test-Driven Migration:**  For each iteration, update and expand unit tests to ensure correct JSON output, parsing, and validation.  Regression testing is crucial after each phase.
*   **Principle 4:  Clear Component Boundaries:** Maintain clear boundaries between components (Claude Synthesis, Gemini Reasoning, Orchestrator) to facilitate independent migration and testing.
*   **Principle 5:  Iterate & Refine Prompts:**  Recognize that prompt engineering for JSON output might require iteration. Be prepared to refine prompts based on model behavior and validation results in each phase.

---

**Iteration 1: Claude Synthesis JSON Migration**

*   **Theme:** Migrate Claude Synthesis to output and process JSON instead of XML. Establish the foundation for JSON-based structured outputs.
*   **Grouped Tasks:**
    1.  **Define `ClaudeSynthesisResult` Pydantic Model (`models/pydantic_schemas.py`):** Create the Pydantic model to represent the JSON structure for Claude Synthesis output.
    2.  **Update Claude Synthesis Prompts for JSON (`claude_integration/claude_client.py`):** Modify prompts in `ClaudeSynthesizer._prepare_message_params` to request JSON output, removing XML instructions.
    3.  **Integrate Langchain `StructuredOutputParser` (`claude_integration/claude_client.py`):** Integrate `StructuredOutputParser` in `ClaudeSynthesizer.generate_code` to parse and validate JSON responses.
    4.  **Update Claude Synthesis Unit Tests for JSON (`test_claude_client.py`):** Update tests to validate JSON output against the `ClaudeSynthesisResult` model and test error handling.
    5.  **Remove XML Validator (`claude_integration/xml_validator.py`, `models/xml_schemas.py`):** Delete `ClaudeXMLValidator` and Claude-specific XML schemas.
*   **Reasoning for Grouping:** This iteration focuses on the critical Claude Synthesis component.  It establishes the core JSON schema, prompt patterns, parsing, and validation mechanisms that will be reused in subsequent iterations. Completing this iteration delivers a functional JSON-based Claude Synthesis and sets the stage for migrating Gemini components.
*   **Information for Developer AI (Example - Task 1.1 - Define `ClaudeSynthesisResult` Pydantic Model):**
    *   **Task Type:** Schema Definition
    *   **Affected Files:** `models/pydantic_schemas.py`, (reference: `models/xml_schemas.py`)
    *   **Project Goals/Iteration Focus:** Establish JSON schema for Claude Synthesis, replace XML schema.
    *   **Implementation Details:**
        *   **Filename:** `models/pydantic_schemas.py`
        *   **Code Snippet Placeholder:**
            ````python
            # models/pydantic_schemas.py
            from pydantic import BaseModel, Field
            from typing import Optional, List

            class SandboxConfig(BaseModel):
                template: Optional[str] = None
                dependencies: Optional[List[str]] = Field(default_factory=list)

            class MetadataItem(BaseModel):
                key: str
                value: str

            class ClaudeSynthesisResult(BaseModel):
                code_completion: str = Field(..., description="Generated code snippet")
                explanation: Optional[str] = Field(None, description="Explanation of code")
                sandbox_config: Optional[SandboxConfig] = None
                metadata: Optional[List[MetadataItem]] = Field(default_factory=list)
                version: str = Field("2.0.0", description="Synthesis version")
            ````
        *   **Component Structure:** Define Pydantic classes `ClaudeSynthesisResult`, `SandboxConfig`, `MetadataItem` with fields mirroring XML schema, using appropriate types (str, Optional, List). Add field descriptions.
        *   **Integration Points:** This schema will be used by Langchain's `StructuredOutputParser` in `ClaudeSynthesizer` and in unit tests for validation.
        *   **Error Handling:** Pydantic validation will handle type errors. Langchain parser will handle JSON parsing errors.
    *   **Agent Selection:** `schema definition agent`

---

**Iteration 2: Gemini Reasoning JSON Migration**

*   **Theme:** Migrate Gemini Reasoning to output and process JSON. Ensure consistent JSON handling for reasoning components.
*   **Grouped Tasks:**
    1.  **Define `GeminiReasoningResult` Pydantic Model (`models/pydantic_schemas.py`):** Create Pydantic model for Gemini Reasoning JSON output.
    2.  **Update Gemini Reasoning Prompts for JSON (`gemini_integration/gemini_client.py`):** Modify prompts in `GeminiReasoner._prepare_prompt` to request JSON output, removing XML instructions.
    3.  **Integrate Langchain `StructuredOutputParser` (`gemini_integration/gemini_client.py`):** Integrate `StructuredOutputParser` in `GeminiReasoner.get_reasoning` for JSON parsing and validation.
    4.  **Update Gemini Reasoning Unit Tests for JSON (`test_gemini_client.py`):** Update tests to validate JSON output against `GeminiReasoningResult` and test error handling.
    5.  **Remove Gemini XML Processor (`gemini_integration/xml_processor.py`, `models/xml_schemas.py`):** Delete `GeminiXMLProcessor` and Gemini-specific XML schemas.
*   **Reasoning for Grouping:** This iteration migrates the Gemini Reasoning component to JSON, mirroring the approach used for Claude Synthesis in Iteration 1. This ensures consistency in JSON handling across both models' reasoning outputs.  It builds upon the foundation established in Iteration 1, reusing Pydantic and Langchain parsing techniques.
*   **Information for Developer AI:** (Similar level of detail as Iteration 1 will be provided in the detailed iteration plan for Phase 2).

---

**Iteration 3: Orchestrator JSON Adaptation**

*   **Theme:** Adapt the `UnifiedOrchestrator` to handle JSON inputs from both Claude and Gemini consistently. Ensure seamless JSON data flow within the orchestrator.
*   **Grouped Tasks:**
    1.  **Review Orchestrator Input Processing (`mvp_orchestrator/orchestrator.py`):** Identify code in `UnifiedOrchestrator` that processes outputs from Claude and Gemini (e.g., in `process_query`).
    2.  **Adapt Orchestrator for JSON Input (`mvp_orchestrator/orchestrator.py`):** Modify the identified code to correctly handle JSON dictionaries (or Pydantic model instances) from both models, instead of XML-processed dictionaries.
    3.  **Update Orchestrator Unit Tests for JSON Input (`test_orchestrator.py`):** Update orchestrator tests to use JSON-based mock inputs from Claude and Gemini and validate correct JSON processing.
    4.  **Refactor Data Handling for Consistency (`mvp_orchestrator/orchestrator.py`):** Refactor data handling within the orchestrator to ensure consistent processing of JSON data regardless of the source model.
    5.  **Integration Testing (Claude+Gemini+Orchestrator):** Perform basic integration tests to verify end-to-end JSON data flow from Claude and Gemini through the Orchestrator.
*   **Reasoning for Grouping:** This iteration focuses on the central orchestrator component. Adapting it to JSON ensures that the entire system can function with JSON outputs from both models. This iteration is crucial for end-to-end JSON compatibility and smooth data flow within the application.
*   **Information for Developer AI:** (Similar level of detail as Iteration 1 will be provided in the detailed iteration plan for Phase 4).

---

**Iteration 4: Gemini Synthesis JSON Migration (If Applicable) & Fallback Strategy**

*   **Theme:** Migrate Gemini Synthesis to JSON (if applicable).  Define and implement a consistent JSON fallback strategy for both models.
*   **Grouped Tasks:**
    1.  **(Conditional) Gemini Synthesis JSON Migration:** If Gemini Synthesis component exists and uses XML, perform tasks similar to Iteration 1 & 2 to migrate it to JSON (Define Pydantic model, update prompts, integrate parser, update tests, remove XML processor). *(Task is conditional based on architecture analysis).*
    2.  **Define JSON Fallback Schemas (`models/pydantic_schemas.py`):** Create Pydantic models for JSON fallback responses for both Claude Synthesis and Gemini Reasoning (and Synthesis if applicable).
    3.  **Implement JSON Fallback Logic (`claude_integration/claude_client.py`, `gemini_integration/gemini_client.py`):** Implement fallback logic in ClaudeSynthesizer and GeminiReasoner (and Synthesis if applicable) to return JSON fallback responses when parsing or validation fails.
    4.  **Update Fallback Unit Tests (`test_claude_client.py`, `test_gemini_client.py`):** Update unit tests to verify correct JSON fallback behavior in error scenarios for both models.
    5.  **Review and Standardize Error Handling:** Review error handling across Claude and Gemini integrations and standardize error reporting and logging for JSON parsing and validation failures.
*   **Reasoning for Grouping:** This iteration addresses the remaining model-specific migration (Gemini Synthesis, if needed) and focuses on robustness by implementing JSON fallback mechanisms.  Consistent fallback and error handling are crucial for a production-ready system.
*   **Information for Developer AI:** (Similar level of detail as Iteration 1 will be provided in the detailed iteration plan for Phase 4).

---

**Iteration 5: Final XML Cleanup & Documentation**

*   **Theme:**  Remove all remaining XML-related code from the codebase. Update documentation to reflect the JSON-based architecture. Finalize the migration.
*   **Grouped Tasks:**
    1.  **Codebase-wide XML Code Review:** Conduct a thorough codebase review to identify and remove any remaining XML-related code, schemas, validators, processors, or dependencies in all modules (`claude_integration`, `gemini_integration`, `models`, `mvp_orchestrator`, etc.).
    2.  **Documentation Update:** Update all relevant documentation (architecture diagrams, component descriptions, API documentation, developer guides) to reflect the JSON-based structured output architecture.
    3.  **Final Integration Testing & Regression Testing:** Perform comprehensive integration testing across all components (Claude, Gemini, Orchestrator) to ensure end-to-end JSON functionality. Run full regression tests to verify no regressions were introduced during the migration.
    4.  **Code Review & Sign-off:** Conduct a final code review of all migrated components and cleanup changes. Obtain sign-off on the completed migration.
    5.  **Deployment & Monitoring:** Deploy the JSON-based system to the target environment. Set up monitoring to track performance and error rates of the JSON-based integrations.
*   **Reasoning for Grouping:** This final iteration focuses on cleanup, documentation, and ensuring the long-term maintainability of the JSON-based system. Removing all XML code simplifies the codebase and reduces technical debt.  Documentation updates ensure clarity and ease of future development. Final testing and deployment ensure a stable and well-documented JSON-based system.
*   **Information for Developer AI:** (Tasks in this iteration are primarily code review, documentation updates, and testing, requiring less detailed developer AI guidance compared to previous iterations).

---

**Future Iterations (Beyond Iteration 5 - High-Level):**

*   **Enhanced JSON Schema Validation:** Explore more advanced JSON schema validation techniques (e.g., using more expressive schema features, custom validation rules) to further improve data integrity and error detection.
*   **Performance Optimization of JSON Parsing:**  If performance becomes a bottleneck, investigate and implement optimizations for JSON parsing and serialization, potentially using more efficient JSON libraries.
*   **Dynamic Prompt Adaptation for JSON:** Explore techniques for dynamically adapting prompts to further improve the reliability and consistency of JSON output from LLMs, potentially based on validation feedback.
*   **Monitoring and Alerting for JSON Errors:** Implement robust monitoring and alerting for JSON parsing and validation errors in production to proactively identify and address issues.
*   **Integration with JSON-based Tools and Libraries:** Explore opportunities to further integrate the system with other JSON-based tools and libraries in the ecosystem to enhance functionality and interoperability.

---

This 5-iteration roadmap provides a structured path for migrating the system from XML to JSON. Each iteration builds upon the previous one, progressively migrating components and ensuring a robust and well-tested JSON-based architecture. The level of detail provided for Iteration 1 aims to be sufficient for guiding both reasoner and developer AIs in the migration process.

`````
