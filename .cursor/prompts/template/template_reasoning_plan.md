---
description: Reasoning and Implementation Plan Template (for Reasoner AI)
---

# Reasoning & Implementation Plan

**Instructions for Reasoner AI:**

> Your task is to generate a detailed implementation plan based on a provided Product Requirements Document (PRD).
>
> Follow the structure below to create the implementation plan. For each key feature and functionality listed in the PRD, break it down into actionable tasks. For each task, provide:
>
> *   **Task Description:** A clear and concise description of the task.
> *   **Affected Files:** List the file paths that will be created or modified. Be specific with file paths and extensions (e.g., `src/components/Button.tsx`, `pages/api/data.ts`).
> *   **Developer AI Guidance:** Provide detailed guidance for a developer AI (or human developer) to implement the task. This should include:
>     *   Component type (e.g., React Functional Component, API endpoint), API endpoint details (path, methods, request/response formats), technology to use (e.g., TypeScript, Next.js API routes), code snippets (demonstrating key logic or structure), data structures (interfaces, schemas), styling guidelines (CSS classes, UI library components), user interaction details (events, states, transitions), etc. Be as specific and actionable as possible.
>     *   **Agent Selection:** Recommend the most appropriate agent type to execute this task (e.g., `frontend component agent`, `backend API agent`, `database migration agent`). Make this prominent and choose from a predefined list of agent types if available.
> *   **Reasoning:** Briefly explain the rationale behind this task and how it contributes to the overall iteration goal and project objectives. Focus on the technical justification and dependencies.
>
> Ensure the plan is comprehensive, detailed, and directly derived from the provided PRD.  Maintain a consistent level of detail and actionable guidance across all tasks.

---

## Iteration Goal (from PRD)

>  *Replace this section with the Iteration Goal from the PRD.*

## Key Features & Functionality Breakdown (from PRD)

> *Replace this section with the Key Features and Functionality list from the PRD.*

## Implementation Tasks & Directives

This section breaks down each key feature into actionable tasks with detailed directives for implementation.

---

### Task 1: [Task Name -  e.g., Implement Topic Input Component (`ControlPanel.tsx`)]

**Task Description:**  *Describe the task clearly and concisely.*
**Affected Files:**  *List file paths to be created or modified.*
**Developer AI Guidance:**
*   *Provide detailed guidance for implementation, including code snippets, technology choices, etc.*
*   **Agent Selection:** `[agent_type]` *Specify the recommended agent type.*
**Reasoning:** *Explain the rationale and contribution of this task.*

---

### Task 2: [Task Name - e.g., Wikipedia API Integration (`pages/api/wiki-search.ts`)]

**Task Description:**  *Describe the task clearly and concisely.*
**Affected Files:**  *List file paths to be created or modified.*
**Developer AI Guidance:**
*   *Provide detailed guidance for implementation, including code snippets, technology choices, etc.*
*   **Agent Selection:** `[agent_type]` *Specify the recommended agent type.*
**Reasoning:** *Explain the rationale and contribution of this task.*

---

// ... Add more Task sections as needed (Task 3, Task 4, etc.) ...

---

**Next Steps:**

1.  **Review and Refine:** Review this generated `reasoning.md` document. Are the tasks clear? Are the directives sufficient?
2.  **Task Assignment (if applicable):** If working with a team, assign these tasks to developers. If working solo, use this as your implementation guide.
3.  **Implementation:** Start implementing the tasks in order.
4.  **Testing & Verification:** As each task is completed, test it against the acceptance criteria in the Lean PRD and the directives in this `reasoning.md` document. 