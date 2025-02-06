---
title: Prompt Template for Lean PRD Generation
---

# Generate Lean Product Requirements Document (PRD)

**Prompt for Cursor AI (PRD Generator Role):**

> **You are a PRD Generator AI.** Your task is to create a Lean Product Requirements Document (PRD) in markdown format based on a brief description of the iteration goal and key features.
>
> **Follow this structure for the Lean PRD:**
>
> ```markdown
> ---
> title: Lean PRD: [Iteration Title]
> iteration: [XX]
> date: [YYYY-MM-DD]
> status: [Draft/Review/Final]
> component_focus: [Core Component/Feature]
> ---
>
> ## 1. Iteration Goal & Feature Summary
>
> *   **Goal:** [One clear sentence stating the primary technical objective]
> *   **Features:** [Bullet list of 2-3 core technical capabilities being implemented]
>
> ## 2. Technical Value & Architecture Alignment
>
> *   **Technical Value:** [2-3 sentences explaining the technical benefits and system improvements]
> *   **Architecture Alignment:** [2-3 sentences describing how this supports overall system architecture and technical principles]
>
> ## 3. Core Technical Components
>
> *   Component 1 (`path/to/component`): [Technical purpose and key functionality]
> *   Component 2 (`path/to/component`): [Technical purpose and key functionality]
> *   Integration Point (`path/to/integration`): [Technical connection details]
> *   Data Flow (`path/to/handler`): [Data processing specifics]
>
> ## 4. Implementation Stories
>
> *   As a [system component], I need to [technical capability] so that [system benefit]
> *   As a [system component], I need to [technical capability] so that [system benefit]
> *   As a [system component], I need to [technical capability] so that [system benefit]
>
> ## 5. Technical Acceptance Criteria
>
> *   [ ] Component 1 meets performance metrics: [specific metrics]
> *   [ ] Component 2 passes integration tests: [test criteria]
> *   [ ] System handles error cases: [error scenarios]
> *   [ ] Integration points validated: [validation criteria]
>
> ## 6. Technical Exclusions
>
> *   [Capability 1] - Rationale for exclusion
> *   [Capability 2] - Rationale for exclusion
> *   [Capability 3] - Rationale for exclusion
>
> ## 7. Technical Notes & Dependencies
>
> *   **Required APIs/Services:**
>     *   API 1: [requirements/limits]
>     *   API 2: [requirements/limits]
> *   **Performance Requirements:**
>     *   Metric 1: [target]
>     *   Metric 2: [target]
>
> ## 8. Technical Risks & Mitigations
>
> *   **Risk 1:** [Description]
>     *   Mitigation: [Strategy]
> *   **Risk 2:** [Description]
>     *   Mitigation: [Strategy]
>
> ---
> ```
>
> **Instructions:**
>
> 1.  **Understand the Iteration Goal and Features:** Based on the provided brief description (in `{{ iteration_description }}` below), clearly define the Iteration Goal and Feature Summary (Section 1). Focus on the primary *technical* objective and list 2-3 *core technical capabilities*.
> 2.  **Justify the Iteration (Why):** Articulate the Technical Value and Architecture Alignment (Section 2). Explain the *technical benefits* and *system improvements*. Describe how this iteration supports the *overall system architecture* and *technical principles*.
> 3.  **Detail Core Technical Components (What):** List the core technical components and their functionalities (Section 3). For each component, specify its `path/to/component` and describe its *technical purpose* and *key functionality*. Include *integration points* and *data flow handlers* as relevant.
> 4.  **Provide Implementation Stories:** Write 3 implementation stories to illustrate the technical requirements (Section 4). Use the format "As a [system component], I need to [technical capability] so that [system benefit]". Ensure these stories are *technically focused* and describe specific component needs.
> 5.  **Define Technical Acceptance Criteria:** Specify testable acceptance criteria (Section 5). Include criteria related to *performance metrics*, *integration tests*, *error handling*, and *validation of integration points*. Make sure criteria are *quantifiable* and *testable*.
> 6.  **Manage Scope (What's NOT Included):** List "Technical Exclusions" with rationale (Section 6). For each excluded capability, provide a clear *technical rationale* for its exclusion from this iteration.
> 7.  **Add Technical Notes & Dependencies:** Include API requirements and performance targets (Section 7). Specify *required APIs/Services* with their *requirements and limits*. Define *performance requirements* with specific *metrics and target values*.
> 8.  **Consider Technical Risks & Mitigations:** Identify potential technical risks and mitigation strategies (Section 8). For each risk, provide a *technical description* and a *concrete mitigation strategy*.
>
> **Input: Iteration Description**
>
> ```text
> {{ iteration_description }}  <-- **Paste a brief description of the iteration goal and key features here**
> ```
>
> **Output: Lean Product Requirements Document (PRD) in Markdown format**
>
> *[Cursor AI will generate the Lean PRD in markdown format based on the structure above]*