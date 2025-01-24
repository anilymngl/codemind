# CodeMind MVP: Intelligent Code Completion Demo - Reasoned Execution (RAT-Inspired)

**Demonstrating Multi-Model AI for Enhanced Code Assistance - Reasoned vs. Executor Architecture**

CodeMind MVP showcases a novel approach to code assistance, inspired by Retrieval Augmented Thinking (RAT). This version emphasizes a **reasoned-executor architecture**, using Google Gemini for strategic reasoning and Anthropic Claude for generating high-quality code completions based on that reasoning.

**🚀 Quickstart: Experience the Demo**

You can run CodeMind MVP in two ways: via a Command-Line Interface (CLI) or through a basic Web API.

**Option 1: Command-Line Interface (CLI)**

1.  **Clone the Repository:**

    ```bash
    git clone [YOUR_REPO_URL_HERE]
    cd codemind_mvp
    ```

2.  **Set API Keys:**

    *   Create a `.env` file in the root directory and add your API keys:

        ```
        GEMINI_API_KEY=YOUR_GEMINI_API_KEY_VALUE
        CLAUDE_API_KEY=YOUR_CLAUDE_API_KEY_VALUE
        ```

3.  **Run the CLI:**

    ```bash
    python rat/rat.py
    ```

4.  **Interact:**

    *   Type your code-related queries.
    *   Use commands like `reasoning` (toggle reasoning visibility), `model <name>` (switch Claude models - if supported in `rat-claude.py` version), and `quit`.

**Option 2: Web API (Basic)**

1.  **Clone the Repository** (if not already done).
2.  **Set API Keys** (if not already done).
3.  **Run the FastAPI Backend:**

    ```bash
    uvicorn backend.main:app --reload
    ```

4.  **Send API Queries:**

    *   Use `curl` or a REST client to send POST requests to `http://127.0.0.1:8000/query` with a JSON payload like `{"user_query": "your code query here"}`.

**Key MVP Features:**

*   **Reasoned Execution Architecture:**  Experience how Gemini provides strategic reasoning, and Claude executes based on that reasoning for more intelligent code assistance.
*   **Transparent Reasoning:** (Toggleable in CLI) See the step-by-step reasoning process from Gemini.
*   **High-Quality Code Completion:** Claude synthesizes code based on best practices and the provided reasoning.
*   **CLI and Web API Demo:**  Interact with CodeMind via a user-friendly CLI or a basic Web API.

**Under the Hood:**

*   **Reasoning Model:** Google Gemini (for strategic analysis and reasoning)
*   **Execution Model:** Anthropic Claude 3.5 Sonnet (for code synthesis and execution)
*   **Backend (API):** FastAPI (Python)
*   **CLI:** Python `prompt_toolkit` and `rich` for interactive interface

**Next Steps & Future Vision:**

This MVP is a foundational step. Future versions will explore:

*   More advanced workflows (debugging, refactoring, testing).
*   Enhanced UI/UX with interactive reasoning exploration.
*   Deeper context awareness and project integration.
*   More sophisticated intent detection for diverse queries.


This project implements a Retrieval Augmented Thinking (RAT) approach, inspired by the work of Skirano.
The core RAT concept is detailed here: [https://github.com/Doriandarko/RAT-retrieval-augmented-thinking]