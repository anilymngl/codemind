---
description: PROJECT_CONTEXT
globs: 
---
# CodeMind - Knowledge Base & Development Directives

This document serves as the central knowledge repository and directive source for CodeMind development. It provides core directives that feed into our template system (`.cursor/prompts/template/*.md`).

## Core System Architecture

### Dual-AI Architecture
- **Reasoning Engine (Gemini):** Strategic planning and reasoning.
- **Executor Engine (Claude):** Code synthesis and explanation.
- **Communication:** XML-based structured data exchange.
- **Processing Flow:** Query → Reasoning Plan → Code Generation → Explanation.

### Template Integration Points
- **Reasoning Plans:** `template_reasoning_plan.md`
  - XML schema for thought process.
  - Required reasoning sections.
  - Example reasoning flows.
  
- **Code Execution:** `template_code_executor.md`
  - Execution environment specs.
  - Safety constraints.
  - Output formatting rules.
  
- **Product Requirements:** `template_lean_prd.md`
  - Feature specification format.
  - Integration requirements.
  - Testing criteria.
  
- **Development Roadmap:** `template_iterative_roadmap.md`
  - Iteration planning.
  - Milestone definitions.
  - Progress tracking.

## Development Directives

### Reasoning Engine (Gemini)
```xml
<reasoning_directives>
    <input_processing>
        - Parse user intent.
        - Extract context clues.
        - Identify constraints.
    </input_processing>
    <planning>
        - Break down into steps.
        - Consider edge cases.
        - Plan error handling.
    </planning>
    <output_format>
        - Use structured XML.
        - Include confidence scores.
        - Provide alternatives.
    </output_format>
</reasoning_directives>
```

### Execution Engine (Claude)
```xml
<execution_directives>
    <code_generation>
        - Follow reasoning plan.
        - Implement safety checks.
        - Add documentation.
    </code_generation>
    <explanation>
        - Link to reasoning.
        - Highlight key decisions.
        - Explain trade-offs.
    </explanation>
    <output_format>
        - Format code cleanly.
        - Include usage examples.
        - Add error handling.
    </output_format>
</execution_directives>
```

## Template System Integration

### Reasoning Plan Template
- **Purpose:** Structure Gemini's thought process.
- **Key Sections:**
  ```xml
  <reasoning_plan>
      <intent_analysis/>
      <approach_planning/>
      <implementation_strategy/>
      <validation_criteria/>
  </reasoning_plan>
  ```

### Code Executor Template
- **Purpose:** Guide Claude's code generation.
- **Key Sections:**
  ```xml
  <code_execution>
      <safety_checks/>
      <implementation/>
      <documentation/>
      <testing/>
  </code_execution>
  ```

### PRD Template Integration
- **Purpose:** Define feature requirements.
- **Key Sections:**
  - Problem Statement.
  - Solution Approach.
  - Implementation Details.
  - Success Criteria.

### Roadmap Template Integration
- **Purpose:** Plan development iterations.
- **Key Sections:**
  - Current Milestone.
  - Next Steps.
  - Future Vision.
  - Progress Metrics.

## Development Guidelines

### Code Quality Standards
- Clean, documented code.
- Comprehensive error handling.
- Performance considerations.
- Security best practices.

### Safety & Security
- Sandbox execution rules.
- Input validation requirements.
- Output sanitization.
- Error recovery procedures.

### Performance Directives
- Response time targets.
- Resource usage limits.
- Optimization priorities.
- Caching strategies.

## Template Usage Instructions

1. **Reasoning Plans**
   - Start with `template_reasoning_plan.md`.
   - Follow XML schema.
   - Include all required sections.
   - Add confidence scores.

2. **Code Execution**
   - Use `template_code_executor.md`.
   - Implement safety checks.
   - Follow output format.
   - Add documentation.

3. **Product Requirements**
   - Reference `template_lean_prd.md`.
   - Define clear objectives.
   - Specify success criteria.
   - Include testing plans.

4. **Development Roadmap**
   - Use `template_iterative_roadmap.md`.
   - Define clear milestones.
   - Set realistic timelines.
   - Track progress metrics.

## Success Criteria & Metrics

### Functionality
- Reasoning plan quality.
- Code generation accuracy.
- Explanation clarity.
- Error handling effectiveness.

### Performance
- Response times.
- Resource utilization.
- Error rates.
- User satisfaction.

### Current Limitations & Future Improvements
- **Sandbox Security:** Basic implementation using `exec()`, needs improvement for production environments (consider containerization or secure sandboxing libraries).
- **Error Handling:** Basic error handling in place; more robust error management and user feedback are needed.
- **Performance:** Initial focus on functionality; optimization is required for complex tasks.
- **Code Quality:** Emphasis on clean, documented code for maintainability and future development.

## Roadmap & Future Considerations

1. **Template Refinement:** Gather user feedback and update templates to improve usability and effectiveness.
2. **UI/UX Enhancement:** Enhance the user interface of the Gradio web application based on user feedback from MVP testing.
3. **Improved Error Handling:** Improve error handling and user feedback in both the CLI and web UI.
4. **Secure Sandboxing:** Explore more secure sandbox options to replace `exec()` for code execution.
5. **Code Analysis Tools:** Consider adding basic code linting or static analysis to the sandbox environment.

## Success Metrics (High-Level)
*   **User Feedback (Qualitative):** Positive initial feedback on the transparency and usefulness of the reasoned code assistant.
*   **Code Quality (Internal):** Clean, modular, and well-documented codebase for future iterations.