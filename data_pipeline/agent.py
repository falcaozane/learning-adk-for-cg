# agent.py

import os
from google.adk import Agent, Workflow
from google.adk.code_executors.built_in_code_executor import BuiltInCodeExecutor
from google.adk.tools import FunctionTool

AGENT_MODEL = "gemini-3.1-flash-lite"

# Instantiate the local built-in code executor
code_executor = BuiltInCodeExecutor()

# # =====================================================================
# # ADK NATIVE HUMAN-IN-THE-LOOP TOOL
# # =====================================================================
# def finalize_gold_data() -> str:
#     """Approves and finalizes the data by renaming temp_gold_data.json to gold_data.json."""
#     if os.path.exists("temp_gold_data.json"):
#         os.rename("temp_gold_data.json", "gold_data.json")
#         return "Successfully finalized and saved gold_data.json for OR-Tools."
#     return "Error: temp_gold_data.json not found."

# # By setting require_confirmation=True, the ADK Web UI will automatically 
# # pause execution and present an "Approve/Reject" UI to the human user 
# # whenever the agent tries to call this tool.
# hitl_save_tool = FunctionTool(
#     finalize_gold_data,
#     require_confirmation=True
# )
# # =====================================================================

EXECUTOR_GUIDELINES = """
# Code Execution Guidelines
- All code snippets provided will be executed within the local sandbox environment.
- **Statefulness:** The variables stay in the environment between executions in a single agent's turn. 
- **Output Visibility:** Always print the output of code execution.
- **Files:** The user will upload files via the chat UI. Use standard Python `os` and `pandas` commands to locate and read them in the current working directory.
- **No Assumptions:** Base findings solely on the data itself. Do not assume column names without checking `df.columns` first if needed.
"""

# 1. Bronze to Silver Agent
bronze_to_silver_agent = Agent(
    name="BronzeToSilverAgent",
    model=AGENT_MODEL,
    code_executor=code_executor, 
    instruction=EXECUTOR_GUIDELINES + """
    **Objective:** You are a Data Engineering Agent. Transform the uploaded scheduling data (Excel or CSVs) into a 'Silver' dataset.
    
    1. Import pandas as pd and os.
    2. Use `os.listdir('.')` to identify the files the user just uploaded.
    3. Load the DataFrames (Orders, Process Flow, Allowed Machines, Machine Details).
    4. Merge Orders with Process Step Flow on 'Product ID'.
    5. Merge the result with Allowed Machine Resource on the process step name.
    6. Convert the string of allowed machines into a Python list (e.g., "SC1, SC2" -> ["SC1", "SC2"]).
    7. Calculate Processing Time: Order Qty (t) / Machine Rate (t/hr).
    8. Save this final dataframe to `silver_data.csv` in the current directory.
    9. Use `print()` to output a summary of the shape and columns of the saved silver data so it is captured for the next agent.
    """
)

# 2. Silver to Gold Agent
silver_to_gold_agent = Agent(
    name="SilverToGoldAgent",
    model=AGENT_MODEL,
    code_executor=code_executor, 
    instruction=EXECUTOR_GUIDELINES + """
    **Objective:** You are an Operations Research Mapping Agent. Map the Silver data to the OR-Tools format and finalize the output.
    
    1. Import pandas and json.
    2. Load `silver_data.csv` from the current directory.
    3. Group the data by 'Order ID'.
    4. Build a dictionary structure where the root has a key "jobs".
    5. Each job should contain 'job_id', 'product_id', 'due_date', and a 'tasks' list.
    6. The 'tasks' list must maintain the chronological sequence of manufacturing steps. 
    7. Save this dictionary directly to a file named `gold_data.json` in the current working directory.
    8. Use `print()` to output a JSON string dump (with indent=2) of the first job.
    9. Finish by sending a friendly final message to the user summarizing that the pipeline is complete, the `silver_data.csv` and `gold_data.json` files have been successfully saved, and present the JSON sample of the first job to them.
    """
)

# 3. HITL Preparation Agent
# hitl_preparation_agent = Agent(
#     name="HITLPreparationAgent",
#     model=AGENT_MODEL,
#     tools=[hitl_save_tool], # Passed into the tools array
#     instruction="""
#     You are a Verification Assistant. 
    
#     **PHASE 1: Presentation**
#     Review the printed JSON summary provided by the SilverToGoldAgent. Present the user with:
#     1. A DATA PIPELINE SUMMARY.
#     2. A GOLD DATA SAMPLE (the JSON printout).
    
#     **PHASE 2: Triggering the Approval Flow**
#     Immediately after presenting the summary, call the `finalize_gold_data` tool to save the dataset.
    
#     *Note: Do not ask the user to type "yes". Because this tool has confirmation enabled at the framework level, calling it will automatically pause execution and prompt the user via the UI to approve or reject the save.*
#     """
# )

# Root workflow 
root_agent = Workflow(
    name="MedallionDataPipelineSystem",
    edges=[(
        "START", 
        bronze_to_silver_agent, 
        silver_to_gold_agent
    )]
)