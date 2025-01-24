# CodeMind MVP: Intelligent Code Completion Demo

**Unleashing the Power of Multi-Model AI for Code Completion (Early Preview)**

CodeMind MVP is a demonstration project exploring a novel approach to intelligent code completion. This early preview showcases a core concept: **leveraging a multi-model AI architecture to generate more insightful and context-aware code suggestions.**

**🚀 Quickstart: Experience the Demo**

Want to see CodeMind MVP in action?  It's quick to run locally!

1.  **Clone the Repository:**

    ```bash
    git clone [YOUR_REPO_URL_HERE]
    cd codemind_mvp
    ```

2.  **Set API Keys:**

    *   You'll need API keys for **Gemini** and **Claude** to run the AI models.
    *   Create a `.env` file in the root directory and add your keys like this:

        ```
        GEMINI_API_KEY=YOUR_GEMINI_API_KEY_VALUE
        CLAUDE_API_KEY=YOUR_CLAUDE_API_KEY_VALUE
        ```
        *(Replace `YOUR_GEMINI_API_KEY_VALUE` and `YOUR_CLAUDE_API_KEY_VALUE` with your actual API keys)*

3.  **Run the FastAPI Backend:**

    Navigate to the `backend` directory and run:

    ```bash
    uvicorn main:app --reload
    ```

4.  **Open the UI:**

    Open your web browser and go to: `http://127.0.0.1:8000`

5.  **Try a Code Completion Query:**

    In the simple web UI, enter a Python code completion query (e.g., `def calculate_average(numbers):`) and click "Get Code Completion."

**Key MVP Features:**

*   **Multi-Model Reasoning (Gemini + Claude):**  Experience a glimpse of how CodeMind combines two AI models for enhanced code completion.
*   **Transparent "Thoughts" (Gemini Reasoning):**  View the raw XML output showing the reasoning process behind the code suggestions (technical preview).
*   **Basic Code Completion Output:**  Generate functional Python code completions (MVP focus).
*   **Minimalist Web UI:**  A very basic web interface to interact with the MVP demo.

**Under the Hood (For Developers):**

CodeMind MVP uses:

*   **Backend:** FastAPI (Python)
*   **Reasoning Model:** Google Gemini (for strategic analysis)
*   **Code Synthesis Model:** Anthropic Claude 3.5 Sonnet (for code generation)

This MVP is a **technical demonstration** and a starting point.  It's designed to showcase the core concept of multi-model reasoning for code completion.

**Next Steps & Future Vision:**

CodeMind is a fun project under active development.  Future versions are planned to explore:

*   More advanced reasoning and code generation capabilities.
*   Deeper IDE integration.
*   Support for more programming languages.
*   Enhanced user interface and features.

