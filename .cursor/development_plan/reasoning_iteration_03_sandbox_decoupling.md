---
description: Reasoning and Implementation Plan for Sandbox Decoupling (Iteration 3)
---

# Reasoning & Implementation Plan: Decouple Sandbox Execution

**Instructions for Reasoner AI:**

> Your task is to generate a detailed implementation plan based on the architectural discussion to decouple sandbox execution from the main query processing flow.
>
> Follow the structure below to create the implementation plan. For each task, provide:
>
> *   **Task Description:** A clear and concise description of the task.
> *   **Affected Files:** List the file paths that will be created or modified. Be specific with file paths and extensions.
> *   **Developer AI Guidance:** Provide detailed guidance for a developer AI (or human developer) to implement the task. Include component type, API endpoint details, technology to use, code snippets, data structures, user interaction details, etc. Be as specific and actionable as possible.
>     *   **Agent Selection:** Recommend the most appropriate agent type to execute this task.
> *   **Reasoning:** Briefly explain the rationale behind this task and how it contributes to the overall iteration goal.

---

## Iteration Goal (from Architectural Discussion)

> Decouple sandbox execution from the main `process_query` flow to improve responsiveness, robustness, and UI flexibility.  Implement a separate `run_sandbox` function and API endpoint that can be triggered by the UI after the initial code generation.

## Key Features & Functionality Breakdown (from Architectural Discussion)

*   **Decouple Sandbox from `process_query`:** Modify `process_query` to no longer execute code in the sandbox.
*   **Create `run_sandbox` Function:** Implement a new method in `UnifiedOrchestrator` to handle sandbox execution.
*   **Create `/run_sandbox` API Endpoint:**  Expose the `run_sandbox` function as a new API endpoint in the backend.
*   **Update UI for Sandbox Execution:** Modify the UI to include a "Run Sandbox" button and handle the separate sandbox execution flow and results.

## Implementation Tasks & Directives

This section breaks down each key feature into actionable tasks with detailed directives for implementation.

---

### Task 1: Modify `process_query` to Decouple Sandbox

**Task Description:**  Modify the `process_query` method in `UnifiedOrchestrator` to remove the sandbox execution step.  `process_query` should now only handle reasoning and code synthesis and return the `OrchestrationResult` with code and reasoning, without waiting for or initiating sandbox execution.
**Affected Files:**  `mvp_orchestrator/enhanced_orchestrator.py`
**Developer AI Guidance:**
*   **Modify `process_query` method:**
    *   Locate the sandbox execution block within the `process_query` method in `mvp_orchestrator/enhanced_orchestrator.py`. This block is currently within an `if synthesis_output.get('code_completion'):` block and starts with `log_info("Attempting code execution in sandbox...")`.
    *   **Remove** the entire `try...except` block that handles sandbox execution, including the `log_info("Attempting code execution in sandbox...")`, `await self.execute_code_in_sandbox(...)`, `sandbox_duration` calculation, `log_performance("sandbox_execution", ...)` and the `except Exception as e:` block for sandbox failures.
    *   Ensure that `process_query` still correctly creates and returns the `OrchestrationResult` after the synthesis phase, including all relevant data (code, reasoning, synthesis output, metadata - but `execution_result` in metadata will now be `None` or explicitly set to indicate no sandbox execution in this flow).
    *   Review the `phase_durations` in the metadata to ensure `sandbox_ms` is conditionally added or set to 0 when sandbox execution is skipped in `process_query`.
*   **Agent Selection:** `backend logic agent`
**Reasoning:** This task is crucial for decoupling the sandbox. By removing the sandbox execution from `process_query`, we ensure that the core query processing flow becomes faster and more robust, focusing solely on reasoning and code generation. This directly addresses the iteration goal of improving responsiveness and robustness.

---

### Task 2: Create `run_sandbox` Function in `UnifiedOrchestrator`

**Task Description:** Implement a new asynchronous method `run_sandbox(self, code: str)` in the `UnifiedOrchestrator` class. This method will encapsulate the logic for executing the provided `code` in the sandbox and return the sandbox execution result.
**Affected Files:**  `mvp_orchestrator/enhanced_orchestrator.py`
**Developer AI Guidance:**
*   **Create `run_sandbox` method:**
    *   Add a new asynchronous method `async def run_sandbox(self, code: str) -> Dict:` to the `UnifiedOrchestrator` class in `mvp_orchestrator/enhanced_orchestrator.py`.
    *   **Move Sandbox Logic:**  Take the sandbox execution logic that was removed from `process_query` in Task 1 and paste it into this new `run_sandbox` method.
    *   **Input Parameter:** The `run_sandbox` method should accept a single argument `code: str`, which is the code to be executed in the sandbox.
    *   **Return Value:** The method should return a dictionary representing the sandbox execution result. This dictionary should have the same structure as the `execution_result` dictionary that was previously used in `process_query` (e.g., `{'success': bool, 'output': Optional[str], 'error': Optional[str], 'details': Optional[Dict]}`).
    *   **Logging and Performance:** Ensure that logging (`log_info`, `log_warning`, `log_error`) and performance tracking (`log_performance`) related to sandbox execution are included within this `run_sandbox` method.  Calculate and log `sandbox_duration` within this method.
*   **Agent Selection:** `backend logic agent`
**Reasoning:** This task creates a dedicated function for sandbox execution, making it reusable and independently callable. This is essential for decoupling the sandbox and allows for a separate API endpoint to be created for UI interaction. This directly supports the iteration goal by providing a modular and decoupled sandbox execution capability.

---

### Task 3: Create `/run_sandbox` API Endpoint in `backend/main.py`

**Task Description:**  Create a new API endpoint `/run_sandbox` in the FastAPI backend (`backend/main.py`). This endpoint will expose the `run_sandbox` function of the `UnifiedOrchestrator` and allow the UI to trigger sandbox execution by sending code to this endpoint.
**Affected Files:**  `backend/main.py`
**Developer AI Guidance:**
*   **Define API Endpoint:**
    *   Open `backend/main.py`.
    *   Use FastAPI decorators to define a new `POST` endpoint at `/run_sandbox`.
    *   This endpoint should be an `async def` function.
    *   **Input:** The endpoint should expect to receive `code: str` in the request body (e.g., as JSON). You can use Pydantic to define a request body model if needed for type validation.
    *   **Call `run_sandbox`:** Inside the endpoint function, get the `code` from the request. Call the `orchestrator.run_sandbox(code)` method (make sure you have access to the `orchestrator` instance in your API endpoint function - likely it's already in scope).
    *   **Return Result:** Return the result from `orchestrator.run_sandbox(code)` as a JSON response. FastAPI will automatically handle the conversion of the returned dictionary to JSON.
    *   **Error Handling:** Wrap the call to `orchestrator.run_sandbox(code)` in a `try...except` block to handle potential exceptions during sandbox execution. Log errors and return appropriate HTTP error responses (e.g., 500 Internal Server Error) with error details if necessary.
*   **Agent Selection:** `backend API agent`
**Reasoning:** This task exposes the sandbox execution functionality through a dedicated API endpoint. This is crucial for allowing the UI to trigger sandbox execution independently of the main query flow. This directly supports the iteration goal by providing the necessary backend infrastructure for decoupled sandbox execution.

---

### Task 4: Update UI to Trigger and Display Sandbox Execution

**Task Description:**  Modify the UI components to add a "Run Sandbox" button that, when clicked, sends a request to the new `/run_sandbox` API endpoint with the generated code.  The UI should then display the results of the sandbox execution in a separate area.
**Affected Files:**  `components/ui_components.py` (or relevant UI component file - identify the file where the code display and interaction logic resides).
**Developer AI Guidance:**
*   **Identify UI Component:** Locate the UI component in your codebase that is responsible for displaying the generated code and handling user interactions (likely in `components/ui_components.py` or a similar file).
*   **Add "Run Sandbox" Button:**
    *   Add a new button (e.g., using Gradio's button component if you are using Gradio, or a similar UI element if using a different framework) next to or below the code display area. Label it "Run Sandbox" or similar.
    *   This button should be initially disabled or hidden until code has been successfully generated and displayed.
*   **Button Click Handler:**
    *   Implement a JavaScript function (if using a web-based UI framework) or a Gradio event handler (if using Gradio) that is triggered when the "Run Sandbox" button is clicked.
    *   **Get Code:**  This handler needs to get the generated code that is currently displayed in the UI.
    *   **Make API Call:** Use `fetch` (in JavaScript) or Gradio's API calling mechanism to make a `POST` request to the `/run_sandbox` API endpoint. Send the generated `code` in the request body (as JSON).
    *   **Display Loading State:** While waiting for the API response, display a loading indicator or message to inform the user that sandbox execution is in progress.
    *   **Handle API Response:**
        *   When the API response is received, parse the JSON response.
        *   Display the sandbox execution results (output and/or error) in a designated area in the UI. This could be a new tab, a collapsible section, or below the code display.
        *   If the sandbox execution was successful, display the output. If it failed, display the error message.
        *   Remove the loading indicator.
*   **Agent Selection:** `frontend component agent` or `UI agent`
**Reasoning:** This task completes the decoupling by providing the UI elements and logic to trigger and display sandbox execution as a separate user-initiated action. This directly addresses the iteration goal of improving UI flexibility and user experience by allowing users to explicitly run the code in the sandbox after reviewing the generated code and reasoning.

---

**Next Steps:**

1.  **Review and Refine:** Review this generated `reasoning.md` document. Are the tasks clear, detailed, and actionable?
2.  **Task Assignment (if applicable):** Assign these tasks to developers.
3.  **Implementation:** Start implementing the tasks in the order presented (Task 1 to Task 4).
4.  **Testing & Verification:** After each task is completed, test it thoroughly. Ensure that `process_query` is faster, sandbox execution is triggered separately via the UI, and the UI correctly displays sandbox results. Verify that the decoupling has been successfully implemented and that the system remains functional and robust. 