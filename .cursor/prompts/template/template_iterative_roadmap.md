---
title: Prompt Template for Iterative Roadmap Generation
---

# Generate Iterative Development Roadmap

**Prompt for Cursor AI (Roadmap Generator Role):**

> **You are a Roadmap Generator AI.** Your task is to create an Iterative Development Roadmap in markdown format for a software project.
>
> **Follow this structure for the Iterative Roadmap:**
>
> ```markdown
> ## [Your Project Name] - Iterative Development Roadmap ([Number] Iterations)
>
> **Guiding Principles for Iteration Design:**
>
> *   **[Principle 1]:**  *(e.g., Build Core Functionality First, Focus on User Experience, Prioritize Performance, etc.)* - Describe the principle in a concise sentence.
> *   **[Principle 2]:**  *(e.g., Vertical Slices, Data-Driven Decisions,  Keep it Simple, etc.)* - Describe the principle in a concise sentence.
> *   **[Principle 3]:**  *(e.g., Logical Dependencies,  Iterate Based on Feedback, Ensure Scalability, etc.)* - Describe the principle in a concise sentence.
> *   **[Principle 4 (Optional)]:** *(e.g., AI-Actionable Detail,  Focus on Modularity, etc.)* - Describe the principle in a concise sentence.
> *   **[Principle 5 (Optional)]:** *(e.g., UI/UX Focus,  Maintainability, etc.)* - Describe the principle in a concise sentence.
>
> ---
>
> **Iteration 1: [Iteration 1 Theme]**
>
> *   **Theme:**  Describe the main focus or goal of Iteration 1 in one sentence.  What key functionality will be established?
> *   **Grouped Tasks:**
>     1.  **[Task 1 Name] (`[ComponentName.tsx or similar]`):** Describe the first task.  Mention the component or file if relevant.
>     2.  **[Task 2 Name] (`[API Endpoint Path or similar]`):** Describe the second task. Mention API endpoint or file if relevant.
>     3.  **[Task 3 Name] (`[ComponentName.tsx or similar]`):** Describe the third task. Mention component or file if relevant.
>     4.  **[Task 4 Name] (`[WorkspacePanel.tsx or similar]`):** Describe the fourth task. Mention component or file if relevant.
>     5.  **[Task 5 Name]:** Describe the fifth task.  *(e.g., Basic Layout & Styling, Initial Data Setup, etc.)*
> *   **Reasoning for Grouping:** Explain *why* these tasks are grouped together in this iteration. What is the logical flow or dependency? What core value does this iteration deliver?
> *   **Information for Developer AI (Example - Task 1.1 - [Task 1 Name]):**  *(Provide an example task breakdown, similar to the WikiTok example, but generalized. Include sections like Task Type, Affected Files, Project Goals/[Relevant Focus], Implementation Details (Filename, Code Snippet Placeholder, Component Props/State, Styling, User Interaction), Agent Selection Placeholder.)*
>
> ---
>
> **Iteration 2: [Iteration 2 Theme]**
>
> *   **Theme:** Describe the main focus or goal of Iteration 2. How does it build upon Iteration 1?
> *   **Grouped Tasks:**
>     1.  **[Task 1 Name] (`[ComponentName.tsx or similar]`):** Describe the first task for Iteration 2.
>     2.  **[Task 2 Name] (`[ComponentName.tsx or similar]`):** Describe the second task for Iteration 2.
>     3.  **[Task 3 Name] (`[API Endpoint Path or similar]`):** Describe the third task for Iteration 2.
>     4.  **[Task 4 Name]:** Describe the fourth task for Iteration 2.
>     5.  **[Task 5 Name]:** Describe the fifth task for Iteration 2.
> *   **Reasoning for Grouping:** Explain the rationale behind grouping these tasks for Iteration 2.
> *   **Information for Developer AI:** *(Mention that you'll provide similar level of detail as Iteration 1, focusing on the new tasks and how they build upon previous iterations.)*
>
> ---
>
> **Iteration 3: [Iteration 3 Theme]**
>
> *   **Theme:** Describe the main focus or goal of Iteration 3.
> *   **Grouped Tasks:**
>     1.  **[Task 1 Name] (`[ComponentName.tsx or similar]`):**
>     2.  **[Task 2 Name] (`[ComponentName.tsx or similar]`):**
>     3.  **[Task 3 Name] (`[API Endpoint Path or similar]`):**
>     4.  **[Task 4 Name]:**
>     5.  **[Task 5 Name]:**
> *   **Reasoning for Grouping:** Explain the rationale.
> *   **Information for Developer AI:** *(Mention level of detail.)*
>
> ---
>
> **(Continue adding Iteration sections for your planned number of iterations - Iteration 4, Iteration 5, etc.)**
>
> ---
>
> **Future Iterations (Beyond Iteration [Last Iteration Number] - High-Level):**
>
> *   **[Future Feature/Enhancement 1]:**  Briefly describe a potential feature or enhancement for future iterations.
> *   **[Future Feature/Enhancement 2]:**  Briefly describe another potential future feature.
> *   **[Future Feature/Enhancement 3]:**  Briefly describe another potential future feature.
> *   **[Future Feature/Enhancement 4 (Optional)]:** Briefly describe another potential future feature.
> *   **[Future Feature/Enhancement 5 (Optional)]:** Briefly describe another potential future feature.
>
> ---
>
> This [Number]-iteration roadmap provides a structured path for developing [Your Project Name]. Each iteration builds upon the previous one, progressively adding features and improving the overall [Project Goal/User Experience]. The level of detail provided for Iteration 1 (and implied for others) aims to be sufficient for guiding both reasoner and developer AIs in the development process.
> ```
>
> **Instructions:**
>
> 1.  **Project Overview:** In `{{ project_overview }}`, provide a brief description of your software project, its goals, and target users.
> 2.  **Number of Iterations:** Decide on the planned number of iterations for your roadmap and replace `[Number]` accordingly.
> 3.  **Guiding Principles:** Define 3-5 Guiding Principles for your iteration design. These should reflect your project's core values and development approach. Consider principles focused on:
>     *   **Fundamental Architecture/Approach:** *(e.g., Microservices Architecture, Event-Driven System)*
>     *   **Development Methodology:** *(e.g., Agile Principles, Test-Driven Development)*
>     *   **Technical Quality:** *(e.g., Code Maintainability, Performance Optimization)*
>     *   **User/Technical Balance:** *(e.g., User Experience Focus, Technical Feasibility)*
>     *   **Long-Term Vision:** *(e.g., Scalability, Extensibility)*
> 4.  **Iteration Themes:** For each iteration (starting with Iteration 1), define a clear Theme that summarizes its main focus. For Iteration 1, consider a theme like "**Core Architecture**" or "**Foundation**" to emphasize building the base of your project.  Provide a paragraph explaining the core focus and critical path for each iteration's theme.
> 5.  **Grouped Tasks:** For each iteration, brainstorm and list 3-5 Grouped Tasks that contribute to the iteration's Theme.  Think in terms of vertical slices of functionality and describe tasks with technical details and clear deliverables. When relevant, mention specific files or paths (e.g., `path/to/file.ext`, `API Endpoint Path`).
> 6.  **Reasoning for Grouping:** Explain the rationale behind the task grouping for each iteration. Detail the technical reasons why these tasks form a cohesive unit and the logical flow or dependencies between them.
> 7.  **Information for Developer AI (Iteration 1 Example):** For Iteration 1, provide a detailed example of "Information for Developer AI" for one task (e.g., Task 1.1).  Expand upon the original example to include details like:
>     *   **Task Type:** Specify the technical category of the task (e.g., "Component Development", "API Integration", "Database Setup").
>     *   **Affected Files:** List complete file paths relevant to the task.
>     *   **Project Goals/[Domain]:** Clearly state the technical objectives and relevant domain for the task.
>     *   **Implementation Details:** Provide granular details:
>         *   **Filename:**  `path/to/file.ext`
>         *   **Code Snippet:** Include a placeholder code snippet demonstrating core implementation ideas, using a relevant language.
>         *   **Component Structure:**  Describe technical specifications or structure if applicable.
>         *   **Integration Points:** Define interface definitions or integration requirements.
>         *   **Error Handling:** Outline potential error scenarios and handling strategies.
>     *   **Agent Selection:**  Specify a suggested agent or tool if relevant (e.g., `[specific_agent].mdc`).
>     This level of detail sets the standard for subsequent reasoning plans.
> 8.  **Future Iterations (High-Level):** Briefly outline potential features or enhancements for future iterations beyond the planned roadmap. Focus on technical enhancements, architectural improvements, performance optimizations, scalability features, and integration capabilities.
>
> **Input: Project Overview**
>
> ```text
> {{ project_overview }}  <-- **Paste a brief overview of your project, goals, and target users here**
> ```
>
> **Output: Iterative Development Roadmap in Markdown format**
>
> *[Cursor AI will generate the Iterative Development Roadmap in markdown format based on the structure above]*

