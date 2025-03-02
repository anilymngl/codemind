---
description: CODEBASE_GUIDE
globs: 
---
# CodeMind MVP - Cursor IDE Helper: Guide & Core Concepts

This guide provides overall project principles and core concepts for CodeMind MVP development. Refer to `Codebase_ProjectContext.mdc` for iteration-specific details and current tasks.

## Project Overview

CodeMind MVP is a **demonstration project for intelligent code completion**. It aims to showcase a **reasoned-executor architecture** using Google Gemini for reasoning and Anthropic Claude for code synthesis.  It goes beyond simple code completion by:

*   **Reasoned Code Completion:** Gemini provides strategic reasoning to guide Claude's code generation.
*   **Transparent Reasoning:** Gemini's thought process is made visible to the user.
*   **High-Quality Code Synthesis:** Claude generates production-ready code based on Gemini's plan.

## Core Concepts

*   **Reasoned-Executor Architecture:**  Separation of reasoning (Gemini) and execution (Claude) for enhanced code assistance.
*   **Retrieval Augmented Thinking (RAT) Inspiration:**  Inspired by RAT principles for multi-model AI collaboration.
*   **XML-Based Communication:** Structured data exchange between Gemini and Claude using XML.
*   **Asynchronous Operations:**  Utilizing `asyncio` for efficient API calls and responsiveness.
*   **Transparent AI Reasoning:**  Emphasis on making the AI's thought process understandable to the user.

## UI/UX Philosophy - Key Principles

*   **Clear Separation of Concerns:** UI layout separates Thoughts, Code, and Reasoning for clarity.
*   **Interactive and User-Friendly:** Gradio Web UI and CLI provide accessible interfaces.
*   **Focus on Transparency:**  Displaying Gemini's reasoning process to build user trust and understanding.

## Key UI Components (High-Level)

*   **`backend/main.py` (Gradio UI):**  Web UI built with Gradio, handles user interaction and displays results.
*   **`rat/rat.py` (CLI):** Command-Line Interface for text-based interaction.
*   **UI Layout (Gradio):** Three-panel layout (Thoughts, Code, Reasoning) for clear information presentation.

## Development Principles

*   **Two-Stage AI Processing:**  Reasoning with Gemini, then Synthesis with Claude.
*   **Structured Communication:** XML for data exchange between AI models.
*   **Asynchronous Programming:**  `asyncio` for non-blocking operations and API calls.
*   **Modular Design:**  Separate modules for Gemini integration, Claude integration, Orchestration, UI, and CLI.
*   **Comprehensive Logging:**  Detailed logging for debugging and monitoring using `logger` module.

## Tech Stack (Concise Summary)

*   **Reasoning Model:** Google Gemini (`gemini-2.0-flash-thinking-exp`)
*   **Synthesis Model:** Anthropic Claude (`claude-3-5-sonnet-20241022` / `claude-3-5-sonnet-20241022`)
*   **Backend Framework:** FastAPI (Python)
*   **UI Framework:** Gradio (Python)
*   **CLI Libraries:** `prompt_toolkit`, `rich` (Python)
*   **Programming Language:** Python

## Out of Scope (MVP)

*   Enhanced Code Generation Features (multi-file, preview, run in CodePen)
*   Advanced UI/UX Improvements (collapsible sections, better highlighting, copy buttons)
*   Persistent History & Context Management
*   Code Management Features (project templates, dependency tracking)
*   Collaboration Features (user accounts, sharing)