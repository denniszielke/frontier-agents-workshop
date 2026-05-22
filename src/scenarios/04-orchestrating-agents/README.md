### Scenario 4 - orchestrating agents using workflows

Goal: In this scenario you will learn how to orchestrate multiple agents and tools using an explicit workflow rather than relying on a single agent to decide every step. You will explore how to break a larger problem into stages, such as gathering user requirements, querying external knowledge, calling specialized agents, and synthesizing a final answer. You will see how the Microsoft Agent Framework workflows help you structure this orchestration, make it testable, and reason about errors or retries at each step. This scenario is relevant because real-world applications often require predictable, auditable flows that coordinate many capabilities, not just a single “black box” model call. By the end, you should understand when to use workflows to gain more control over how and when different agents and tools are invoked.

Task:
- Design a simple end-to-end workflow that coordinates at least two capabilities (for example, a weather agent and a planning or summarization agent) to answer a composite user request.
- Implement the workflow using the provided workflow samples so that each stage is explicit (e.g., gather input, call agent A, call agent B, aggregate results).
- Configure the workflow to handle common failure cases, such as a missing location or an unavailable downstream agent, and provide user-friendly error messages.
- Add basic logging or tracing so you can see which workflow steps ran for a given user query.
- Run and iterate on your workflow to confirm that changing one step’s behavior is isolated and easy to reason about.

Relevant references
- (Add link to Microsoft Agent Framework workflow documentation used in your environment.)

Relevant samples:
- [`samples/workflows/generation-workflow.py`](../../../samples/workflows/generation-workflow.py) – example of structuring a generation task as a workflow.
- [`samples/workflows/parallel-agents.py`](../../../samples/workflows/parallel-agents.py) – example of coordinating multiple agents in parallel.
- [`samples/simple-agents/basic-agent.py`](../../../samples/simple-agents/basic-agent.py) – simple agent you can plug into workflow steps.

Input queries:
- "Plan my day tomorrow including where I should go based on the weather and give me a short summary."
- "Check the weather for the weekend and then propose two activities that fit the conditions."
- "If one of the agents fails, explain which step failed and what you tried to do."

Tooling tips:
Start by running `generation-workflow.py` and `parallel-agents.py` to see how workflows are declared and executed in code. Identify clear stages in your scenario (for example, "collect user preferences", "check weather", "propose plan") and map each stage to a function or agent call. Use the workflow constructs to control sequencing, branching, or simple parallelism rather than embedding that logic directly inside a single agent prompt. When troubleshooting, log the input and output of each workflow step so you can trace how a user query moves through the system. Keep the workflow small and focused; the goal is to understand orchestration patterns, not to build a full production planner.

Your role should be "user" in the inputs

