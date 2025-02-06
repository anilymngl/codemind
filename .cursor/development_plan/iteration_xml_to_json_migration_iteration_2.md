---
description: Iteration Plan for XML to JSON Migration - Iteration 2: Gemini Reasoning JSON Migration
---

# Iteration Plan: XML to JSON Migration - Iteration 2: Gemini Reasoning JSON Migration

**Instructions for Iteration 2:**

> Your task is to execute Iteration 2 of the XML to JSON migration roadmap: **Migrate Gemini Reasoning to JSON**. This involves defining the JSON schema for Gemini Reasoning output, updating prompts, integrating a JSON parser, updating unit tests, and removing the XML processor for Gemini Reasoning.
>
> Follow the structure below to execute this iteration. For each task, you will:
>
> *   **Task Description:** A clear and concise description of the migration task.
> *   **Affected Files:** List the file paths that will be created or modified. Be specific with file paths and extensions.
> *   **Developer AI Guidance:** Provide detailed guidance for a developer (or AI) to implement the task. This should include:
>     *   Specific steps to take, code examples, libraries to use (Pydantic, Langchain), and references to relevant documentation or previous iteration plans.
>     *   Highlight areas where careful attention is needed, such as prompt updates, parsing logic changes, and test modifications.
> *   **Reasoning:** Briefly explain the rationale behind this task and how it contributes to the overall goal of migrating from XML to JSON for Gemini Reasoning and the broader migration roadmap.

---

## Iteration Goal (from Roadmap - Iteration 2)

> Migrate Gemini Reasoning to output and process JSON instead of XML. Ensure consistent JSON handling for reasoning components.

## Key Tasks (from Roadmap - Iteration 2)

> 1.  Define `GeminiReasoningResult` Pydantic Model (`models/pydantic_schemas.py`)
> 2.  Update Gemini Reasoning Prompts for JSON (`gemini_integration/gemini_client.py`)
> 3.  Integrate Langchain `StructuredOutputParser` (`gemini_integration/gemini_client.py`)
> 4.  Update Gemini Reasoning Unit Tests for JSON (`test_gemini_client.py`)
> 5.  Remove Gemini XML Processor (`gemini_integration/xml_processor.py`, `models/xml_schemas.py`)

## Implementation Tasks & Directives

This section breaks down Iteration 2 into actionable tasks with detailed directives for implementation.

---

### Task 1: Define `GeminiReasoningResult` Pydantic Model (`models/pydantic_schemas.py`)

**Task Description:** Create a Pydantic model (`GeminiReasoningResult`) in `models/pydantic_schemas.py` to represent the desired JSON structure for Gemini Reasoning output. This model will replace the current XML schema used for Gemini Reasoning.
**Affected Files:**
*   `models/pydantic_schemas.py` (modification)
*   `models/xml_schemas.py` (reference for existing XML schema structure - `GEMINI_REASONING_SCHEMA`)
**Developer AI Guidance:**
*   **Modify `models/pydantic_schemas.py`:** Open the existing `models/pydantic_schemas.py` file.
*   **Define `GeminiReasoningResult` Model:**  In `models/pydantic_schemas.py`, define the `GeminiReasoningResult` Pydantic model.  Refer to the existing `GEMINI_REASONING_SCHEMA` in `models/xml_schemas.py` to understand the required fields. Based on the XML schema, the key fields are likely to include elements like `reasoning_steps` (a list of reasoning steps), `conclusion`, and potentially metadata. Use appropriate Pydantic field types (e.g., `List[str]`, `str`, `Optional[str]`, `List[MetadataItem]`). Ensure you include descriptions for each field. You might need to define nested Pydantic models if `reasoning_steps` or other fields have a complex structure.
*   **Example Pydantic Model Structure (Conceptual - adapt based on `GEMINI_REASONING_SCHEMA`):**
    ````python
    # models/pydantic_schemas.py
    from pydantic import BaseModel, Field
    from typing import Optional, List

    class MetadataItem(BaseModel): # Assuming MetadataItem is already defined from Iteration 1
        key: str
        value: str

    class GeminiReasoningResult(BaseModel):
        reasoning_steps: List[str] = Field(..., description="List of reasoning steps")
        conclusion: str = Field(..., description="Final conclusion of reasoning")
        metadata: Optional[List[MetadataItem]] = Field(default_factory=list)
        version: str = Field("2.0.0", description="Reasoning version")
    ````
*   **Agent Selection:** `schema definition agent`
**Reasoning:** Defining the `GeminiReasoningResult` Pydantic model is the first step in Iteration 2. This model will define the structure for JSON output from Gemini Reasoning and will be used for parsing and validation in subsequent tasks, mirroring the approach taken for Claude Synthesis in Iteration 1. It directly addresses Task 1 of the Iteration 2 goals in the roadmap.

---

### Task 2: Update Gemini Reasoning Prompts for JSON Output (`gemini_integration/gemini_client.py`)

**Task Description:** Modify the prompt construction in `GeminiReasoner._prepare_prompt` to instruct Gemini to output JSON instead of XML.  Incorporate best practices for prompting for JSON output, similar to the Claude prompt updates in Iteration 1.
**Affected Files:**
*   `gemini_integration/gemini_client.py` (specifically `GeminiReasoner._prepare_prompt`)
**Developer AI Guidance:**
*   **Locate `_prepare_prompt`:** Open `gemini_integration/gemini_client.py` and find the `_prepare_prompt` method within the `GeminiReasoner` class.
*   **Modify Prompt Template:**  Update the prompt template within this method.
    *   **Remove XML Instructions:**  Completely remove the section in the prompt that instructs Gemini to "Respond in XML format..." and the XML structure example.
    *   **Add JSON Instruction:** Add a clear instruction for JSON output at the beginning of the response instructions. For example: "Respond in JSON format. The JSON response should conform to the following structure:".
    *   **Provide JSON Structure Example:**  Include a simplified example of the JSON structure you expect, mirroring the `GeminiReasoningResult` Pydantic model. Represent this as a code block within the prompt using backticks. Use `<>` tags around the JSON structure elements for template guidance, if appropriate for Gemini prompting.
*   **Example Prompt Snippet (Conceptual - adapt based on current prompt):**
    ````python
    prompt = f"""
    You are a helpful AI reasoning assistant. Please provide a step-by-step reasoning to answer the user's question.

    QUESTION: {user_question}

    Respond in JSON format. The JSON response should conform to the following structure:
    ```json
    {{
      "reasoning_steps": ["<step 1>", "<step 2>", "..."],
      "conclusion": "<final conclusion>",
      "metadata": [
        {{ "key": "...", "value": "..." }}
      ]
    }}
    ```
    ... (rest of the prompt) ...
    """
    ````
*   **Agent Selection:** `prompt engineering agent`
**Reasoning:** Updating the prompts is essential to guide Gemini to generate JSON output for reasoning. Clear and explicit prompts are crucial for achieving consistent structured outputs from LLMs. This task directly addresses Task 2 of Iteration 2 and ensures Gemini Reasoning is configured for JSON output.

---

### Task 3: Integrate Langchain `StructuredOutputParser` (`gemini_integration/gemini_client.py`)

**Task Description:** Integrate Langchain's `StructuredOutputParser` and the `GeminiReasoningResult` Pydantic model into `GeminiReasoner.get_reasoning` to parse and validate Gemini's JSON responses.
**Affected Files:**
*   `gemini_integration/gemini_client.py` (`GeminiReasoner.get_reasoning`, `_handle_response`, `_handle_stream_response`, `__init__`)
*   `models/pydantic_schemas.py` (to import `GeminiReasoningResult`)
**Developer AI Guidance:**
*   **Ensure Langchain and Pydantic are installed:** (These should already be installed from Iteration 1).
*   **Import Necessary Classes:** In `gemini_integration/gemini_client.py`, import `StructuredOutputParser` from `langchain.output_parsers` and `GeminiReasoningResult` from `models.pydantic_schemas`.
    ````python
    from langchain.output_parsers import StructuredOutputParser
    from models.pydantic_schemas import GeminiReasoningResult
    ````
*   **Initialize `StructuredOutputParser` in `GeminiReasoner.__init__`:** Initialize `StructuredOutputParser` as an instance variable in the `GeminiReasoner` class constructor, similar to how it was done for `ClaudeSynthesizer` in Iteration 1.
    ````python
    # gemini_integration/gemini_client.py
    class GeminiReasoner:
        def __init__(self, gemini_key: str):
            # ... existing code ...
            self.output_parser = StructuredOutputParser(pydantic_object=GeminiReasoningResult)
            # ... existing code ...
    ````
*   **Parse JSON Response in `_handle_response` and `_handle_stream_response`:**
    *   **Remove XML Processing:**  Remove the calls to `self.xml_processor.process_xml_response(response_text)` in both `_handle_response` and `_handle_stream_response`.
    *   **Parse JSON with `self.output_parser.parse()`:**  Replace the XML processing with JSON parsing using `self.output_parser.parse(response_text)`.  The `response_text` is the raw text output from Gemini. This will return an instance of `GeminiReasoningResult` if parsing and validation are successful.
    *   **Handle `ParseError`:**  Wrap the `self.output_parser.parse()` call in a `try...except` block to catch `ParseError` exceptions from Langchain.  If a `ParseError` occurs, log the error and raise a `ReasoningError` exception (or the appropriate error type for Gemini Reasoning).
    *   **Update Return Value:**  Modify the return statements in `_handle_response` and `_handle_stream_response` to return the parsed `GeminiReasoningResult` object as the `result`.
*   **Example Parsing Snippet (Conceptual):**
    ````python
    # in _handle_response or _handle_stream_response
    try:
        parsed_output = self.output_parser.parse(response_text) # response_text is Gemini's raw text response
        log_debug("Successfully parsed JSON output using Langchain for Gemini Reasoning")
        return parsed_output
    except ParseError as e:
        log_error(f"JSON parsing failed for Gemini Reasoning: {e}")
        raise ReasoningError("Failed to parse JSON output from Gemini Reasoning", details={'error': str(e), 'raw_output': response_text, 'parser_error': str(e)})
    ````
*   **Agent Selection:** `integration agent`, `error handling agent`
**Reasoning:** Integrating Langchain's `StructuredOutputParser` is essential for robustly parsing and validating the JSON output from Gemini Reasoning. This mirrors the approach used for Claude Synthesis in Iteration 1 and ensures consistent JSON parsing and validation across both models. This task directly addresses Task 3 of Iteration 2.

---

### Task 4: Update Gemini Reasoning Unit Tests for JSON (`test_gemini_client.py`)

**Task Description:** Update the unit tests in `test_gemini_client.py` to test the JSON-based output of `GeminiReasoner` and validate against the `GeminiReasoningResult` Pydantic model.
**Affected Files:**
*   `test_gemini_client.py`
*   `models/pydantic_schemas.py` (to import `GeminiReasoningResult` for assertions)
**Developer AI Guidance:**
*   **Locate Relevant Tests:** Open `test_gemini_client.py` and identify the tests that target the `GeminiReasoner` and its output (likely tests for `get_reasoning` method).
*   **Update Mock Responses:** Modify the mock responses used in the tests to be valid JSON strings that conform to the structure defined by the `GeminiReasoningResult` Pydantic model.  Ensure the mock JSON responses include all the fields defined in the model (`reasoning_steps`, `conclusion`, `metadata`).
*   **Update Assertions:**  Change the assertions in the tests to:
    *   **Assert Output Type:** Assert that the output of `GeminiReasoner.get_reasoning` is an instance of the `GeminiReasoningResult` Pydantic model.
    *   **Validate Field Values:** Assert that the fields within the output object (e.g., `output.reasoning_steps`, `output.conclusion`) have the expected values from the mock response.
    *   **Test Error Cases:**
        *   **Invalid JSON Response:** Mock Gemini to return a string that is *not* valid JSON.  Assert that `GeminiReasoner.get_reasoning` raises a `ReasoningError` or handles the parsing error appropriately.
        *   **JSON Non-conforming to Schema:** Mock Gemini to return valid JSON, but JSON that *does not* conform to the `GeminiReasoningResult` Pydantic model (e.g., missing required fields, incorrect data types). Assert that parsing/validation fails and an error is handled.
*   **Example Test Update Snippet (Conceptual):**
    ````python
    # test_gemini_client.py
    from models.pydantic_schemas import GeminiReasoningResult
    from mvp_orchestrator.error_types import ReasoningError # Or appropriate Gemini error type
    import pytest

    async def test_gemini_reasoner_get_reasoning_json_output(mock_gemini_client): # Assuming mock client setup
        mock_gemini_client.return_value.generate_content.return_value = MockGeminiResponse( # Assuming mock response
            text='{"reasoning_steps": ["Step 1", "Step 2"], "conclusion": "Test Conclusion", "metadata": []}' # Mock JSON response
        )
        reasoner = GeminiReasoner(gemini_key="test_key")
        output = await reasoner.get_reasoning("Test question")

        assert isinstance(output, GeminiReasoningResult) # Assert output is Pydantic model
        assert output.reasoning_steps == ["Step 1", "Step 2"]
        assert output.conclusion == "Test Conclusion"
        # ... assert other fields ...

    async def test_gemini_reasoner_get_reasoning_invalid_json(mock_gemini_client):
        mock_gemini_client.return_value.generate_content.return_value = MockGeminiResponse(
            text='This is not valid JSON' # Mock invalid JSON
        )
        reasoner = GeminiReasoner(gemini_key="test_key")
        with pytest.raises(ReasoningError): # Assert error is raised
            await reasoner.get_reasoning("Question that will fail")
    ````
*   **Agent Selection:** `testing agent`, `validation agent`
**Reasoning:** Updating unit tests is crucial to ensure that the migration of Gemini Reasoning to JSON output is successful and doesn't introduce regressions.  Tests that validate against the `GeminiReasoningResult` Pydantic model will provide confidence that the JSON parsing and validation are working correctly and that the `GeminiReasoner` is producing the expected structured output. This task directly addresses Task 4 of Iteration 2.

---

### Task 5: Remove Gemini XML Processor (`gemini_integration/xml_processor.py`, `models/xml_schemas.py`)

**Task Description:** Remove the `GeminiXMLProcessor` class, the Gemini-specific XML schema parts from `models/xml_schemas.py`, and any remaining XML-specific code in `gemini_integration/gemini_client.py`.
**Affected Files:**
*   `gemini_integration/xml_processor.py` (to be deleted)
*   `models/xml_schemas.py` (remove Gemini-specific XML schemas and fallback templates - `GEMINI_REASONING_SCHEMA`, `GEMINI_FALLBACK_TEMPLATE`)
*   `gemini_integration/gemini_client.py` (remove import of `GeminiXMLProcessor` and any XML-specific cleanup code if any remains)
**Developer AI Guidance:**
*   **Delete `gemini_integration/xml_processor.py`:**  Completely delete the file `gemini_integration/xml_processor.py`.
*   **Modify `models/xml_schemas.py`:** Open `models/xml_schemas.py`.
    *   **Remove Gemini-Specific Schemas:** Delete the `GEMINI_REASONING_SCHEMA` and `GEMINI_FALLBACK_TEMPLATE` definitions.
    *   **Review Remaining Schemas:** After removing Gemini-specific schemas, review if `models/xml_schemas.py` still contains any relevant XML schemas. If it becomes empty or only contains Claude-specific schemas (which are also being migrated away from), consider if the file itself is still needed or can be removed in a later iteration if no longer used. For now, just remove Gemini-specific parts.
*   **Modify `gemini_integration/gemini_client.py`:**
    *   **Remove Import:** Remove the line `from .xml_processor import GeminiXMLProcessor` from the imports at the top of the file.
    *   **Remove Processor Instantiation:**  Delete the line in `GeminiReasoner.__init__` that instantiates `self.xml_processor = GeminiXMLProcessor()`.
    *   **Remove XML Cleanup Code:**  Check `_handle_response` and `_handle_stream_response` for any remaining XML-specific cleanup code (e.g., code that removes XML declarations or markdown XML code blocks).  These should be removed as the parsing is now handled by Langchain and we are expecting JSON.
*   **Agent Selection:** `cleanup agent`, `refactoring agent`
**Reasoning:**  This task completes Iteration 2 by removing the obsolete Gemini XML processor and schemas.  This cleanup step simplifies the codebase, removes dependencies on XML processing for Gemini Reasoning, and ensures that Gemini Reasoning is now fully based on JSON for its structured outputs. This task directly addresses Task 5 of Iteration 2 and contributes to the overall cleanup and simplification goals of the migration.

---

**Next Steps for Iteration 2:**

1.  **Review and Refine:** Review this `iteration_2_gemini_reasoning_json_migration.md` document. Ensure tasks are clear, directives are sufficient, and no steps are missing for Iteration 2.
2.  **Task Assignment (if applicable):** Assign these tasks to developers or prepare for self-implementation.
3.  **Implementation:** Start implementing tasks in order (Task 1 to Task 5).
4.  **Testing & Verification:** After each task, run unit tests in `test_gemini_client.py` to verify changes. Ensure all tests pass after completing all tasks in Iteration 2.
5.  **Commit Changes:** Once all tasks are implemented and tested, commit the changes for Iteration 2 to version control.
6.  **Proceed to Iteration 3 Planning:** After successful completion of Iteration 2, begin planning for **Iteration 3: Orchestrator JSON Adaptation**, using the `xml_to_json_migration_roadmap.md` and `template_reasoning_plan.md` to create `iteration_3_orchestrator_json_adaptation.md`.

`````

This `iteration_2_gemini_reasoning_json_migration.md` file provides a detailed, actionable plan for executing Iteration 2 of the XML to JSON migration roadmap. It breaks down the iteration goal into five key tasks with clear directives and reasoning for each, mirroring the structure and detail of the Iteration 1 plan.

Please review this iteration plan and let me know if it's ready for implementation or if you have any feedback or adjustments!
