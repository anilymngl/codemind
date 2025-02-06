# CodeMind MVP: Intelligent Code Completion Demo - Reasoned Execution (RAT-Inspired)

**Demonstrating Multi-Model AI for Enhanced Code Assistance - Reasoned vs. Executor Architecture**

CodeMind MVP showcases a novel approach to code assistance, inspired by Retrieval Augmented Thinking (RAT). This version emphasizes a **reasoned-executor architecture**, using Google Gemini for strategic reasoning and Anthropic Claude for generating high-quality code completions.

**🚀 Quickstart: Experience the Demo**

*   **[Option 1: Command-Line Interface (CLI)](#option-1-command-line-interface-cli)**
*   **[Option 2: Web API (Basic)](#option-2-web-api-basic)**

**Key MVP Features:**

*   **Reasoned Execution Architecture:** Gemini reasoning + Claude execution.
*   **Transparent Reasoning:** See Gemini's thought process (CLI).
*   **High-Quality Code Completion:** Claude-synthesized code.
*   **CLI and Web API Demo:**  User-friendly interfaces.

**Documentation:**

*   **[Project Requirements Document (PRD)](docs/PROJECT_REQUIREMENTS.md):**  Detailed project goals, features, architecture, and tech stack.
*   **[Roadmap](docs/ROADMAP.md):**  Development phases, future vision, and release timeline.
*   **[Design Decisions Log](docs/DESIGN_DECISIONS_LOG.md):**  Rationale and trade-offs for key design choices.
*   **[System Prompts](docs/SYSTEM_PROMPTS.md):**  Details of prompts used for Gemini and Claude.
*   **[File Structure](docs/FILE_STRUCTURE.md):**  Overview of project directories and files.
*   **[Development Tasks](docs/DEVELOPMENT_TASKS.md):**  Detailed task breakdown for each development phase.

**Under the Hood:**

*   **Reasoning Model:** Google Gemini
*   **Execution Model:** Anthropic Claude 3.5 Sonnet
*   **Backend (API):** FastAPI (Python)
*   **CLI:** Python `prompt_toolkit` and `rich`

**Get Started:**

**(Keep the Quickstart instructions for CLI and Web API as in the original `README.md`, but potentially shorten them if they are too verbose. Link to more detailed setup instructions in the PRD or a separate SETUP.md if needed.)**

**Option 1: Command-Line Interface (CLI)**

1.  **Clone the Repository:** `git clone [YOUR_REPO_URL_HERE]`
2.  **Set API Keys:** Create `.env` file with `GEMINI_API_KEY` and `CLAUDE_API_KEY`.
3.  **Run the CLI:** `python rat/rat.py`
4.  **Interact:** Type queries, use `reasoning`, `model`, `quit` commands.

**Option 2: Web API (Basic)**

1.  **Clone & Set API Keys** (as above).
2.  **Run FastAPI Backend:** `uvicorn backend.main:app --reload`
3.  **Send API Queries:** Use `curl` or REST client to `http://127.0.0.1:8000/query`.

**Next Steps & Future Vision:**

**(Keep the "Next Steps & Future Vision" section from the original `README.md` or condense it.)**

This MVP is a foundational step. Future versions will explore more advanced workflows, enhanced UI/UX, deeper context awareness, and more sophisticated intent detection.

**(Keep the RAT inspiration and link as in the original `README.md`)**

---
**End of README.md**