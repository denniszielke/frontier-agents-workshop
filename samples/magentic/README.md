# Exercise 4: Magentic Basics

This exercise demonstrates Magentic orchestration - an advanced multi-agent coordination pattern that automatically manages task decomposition, agent selection, and result synthesis. Unlike concurrent or sequential patterns, Magentic uses an intelligent orchestrator that:

- Plans how to decompose the task
- Delegates subtasks to appropriate agents
- Monitors progress and adapts the plan
- Synthesizes final results

It is based on the (Magentic One concept)[https://www.microsoft.com/en-us/research/articles/magentic-one-a-generalist-multi-agent-system-for-solving-complex-tasks/?msockid=0493d15deb436a993cebc291eaef6baa] which was originally implemented with autogen. This exercise uses the agent-framework MagenticBuilder API to achieve similar functionality, as the [Magentic One](https://learn.microsoft.com/en-us/agent-framework/user-guide/workflows/orchestrations/magentic?pivots=programming-language-python) concept is also implemented in the framework using the [MagenticBuilder class](https://learn.microsoft.com/en-us/python/api/agent-framework-core/agent_framework.magenticbuilder?view=agent-framework-python-latest).

![magentic](image.png)

## Key Concepts

1. MagenticBuilder: High-level API for multi-agent orchestration
2. Standard Manager: Built-in orchestrator with planning capabilities
3. Specialized Agents: Domain experts (Researcher, Coder)
4. Streaming Callbacks: Real-time event monitoring
5. Event Types: Orchestrator messages, agent deltas, agent messages, final results

## Workflow Parameters

- max_round_count: Maximum orchestration rounds (default: 10)
- max_stall_count: Retries when progress stalls (default: 3)
- max_reset_count: Full plan resets allowed (default: 2)

## Prerequisites

- OpenAI API key configured: OPENAI_API_KEY environment variable
- Agent Framework installed: pip install agent-framework
- Special models for some agents:
  - ResearcherAgent: gpt-4o-search-preview (web search capability)
  - CoderAgent: OpenAI Assistants with code interpreter


## Setup

1. Clone the repository and navigate to the `samples/magentic` directory.
2. Create a virtual environment and install dependencies:

   ```bash
   python -m venv .agentic
   source .agentic/bin/activate  # On Windows use `.agentic\Scripts\activate`
   pip install -r requirements.txt
   ```

3. Copy the `.env.example` to `.env` and set your Azure OpenAI endpoint and deployment names:

   ```bash
    cp .env.example .env
    ```

4. Edit the `.env` file to include your Azure OpenAI endpoint and deployment names.
5. Run the Magentic orchestration script:

   ```bash
   python main.py
   ```

6. Observe the console output for real-time orchestration events and the final synthesized result.

## Notes

you need a model capable of searching in the internet to get the better results with the ResearcherAgent. If you have access to gpt-4o-search-preview, use it. Otherwise, you can use gpt-4o or any other model you have access to, but the results may vary. Additionally, you could add a tool to research the web, but the results won't also be as good as with a model with search capabilities.