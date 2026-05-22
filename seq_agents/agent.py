import datetime
from zoneinfo import ZoneInfo
from dotenv import load_dotenv
from google.adk import Agent
from google.adk.agents import SequentialAgent
from google.adk.models.lite_llm import LiteLlm
from google.adk.tools import google_search
from ddgs import DDGS
from google.adk import Workflow

load_dotenv()

#AGENT_MODEL = "ollama/deepseek-r1:8b"

model = LiteLlm(
    model="groq/llama-3.3-70b-versatile",  # use "groq/<groq-model-name>"
)

def get_current_time(city:str) -> dict:
    """Returns the current time in a specified city.

    Args:
        city (str): The name of the city for which to retrieve the current time.

    Returns:
        dict: status and result or error msg.
    """

    if city.lower() == "new york":
        tz_identifier = "America/New_York"
    else:
        return {
            "status": "error",
            "error_message": (f"Sorry, I don't have timezone information for {city}."),
        }

    tz = ZoneInfo(tz_identifier)
    now = datetime.datetime.now(tz)
    report = f'The current time in {city} is {now.strftime("%Y-%m-%d %H:%M:%S %Z%z")}'
    return {"status": "success", "report": report}

def web_search(query: str) -> dict:
    """Performs a web search using DuckDuckGo and returns the results.

    Args:
        query (str): The search query.

    Returns:
        dict: status and search results or error message.
    """
    try:
        results = []
        for r in DDGS().text(query, max_results=5):
            results.append({"title": r["title"], "href": r["href"], "body": r["body"]})
        return {"status": "success", "results": results}
    except Exception as e:
        return {"status": "error", "error_message": str(e)}
    

# -- Sequential Agent ---
# Destination Research Agent - Researches location information
destination_research_agent = Agent(
    name="DestinationResearchAgent",
    model=model,
    tools=[web_search],
    description="An agent that researches travel destinations and gathers essential information",
    instruction="""
    You are a travel researcher. You will be given a destination and travel preferences, and you will research:
    - Best time to visit and weather patterns
    - Top attractions and must-see locations
    - Local culture, customs, and etiquette tips
    - Transportation options within the destination
    - Safety considerations and travel requirements
    Provide comprehensive destination insights for trip planning.
    """,
    output_key="destination_research",
)

# Itinerary Builder Agent - Creates detailed travel schedule
itinerary_builder_agent = Agent(
    model=model,
    name="ItineraryBuilderAgent",
    description="An agent that creates structured travel itineraries with daily schedules",
    instruction="""
    You are a professional travel planner. Using the research from "destination_research" output, create a detailed itinerary that includes:
    - Day-by-day schedule with recommended activities
    - Suggested accommodation areas or districts
    - Estimated time requirements for each activity
    - Meal recommendations and dining suggestions
    - Budget estimates for major expenses
    Structure it logically for easy following during the trip.
    """,
    output_key="travel_itinerary",
)

# Travel Optimizer Agent - Adds practical tips and optimizations
travel_optimizer_agent = Agent(
    model=model,
    name="TravelOptimizerAgent",
    description="An agent that optimizes travel plans with practical advice and alternatives",
    instruction="""
    You are a seasoned travel consultant. Using the itinerary from "travel_itinerary" output, optimize it by adding:
    - Money-saving tips and budget alternatives
    - Packing recommendations specific to the destination
    - Backup plans for weather or unexpected situations
    - Local apps, websites, or resources to download
    - Cultural do's and don'ts for respectful travel
    
    Format the final output as:
    
    ITINERARY: {travel_itinerary}
    
    OPTIMIZATION TIPS: [your money-saving and practical tips here]
    
    TRAVEL ESSENTIALS: [packing and preparation advice here]
    
    BACKUP PLANS: [alternative options and contingencies here]
    """,
)



root_agent = Workflow(
    name = "travel_planner_System",
    edges=[(
        "START", 
        destination_research_agent, 
        itinerary_builder_agent, 
        travel_optimizer_agent
    )]
)

# root_agent = SequentialAgent(
#     name="TravelPlanningSystem",
#     # model=LiteLlm(AGENT_MODEL),#not needed for SequentialAgent
#     # model=AGENT_MODEL, #not needed for SequentialAgent
#     description="A comprehensive system that researches destinations, builds itineraries, and optimizes travel plans",
#     sub_agents=[
#         destination_research_agent,
#         itinerary_builder_agent,
#         travel_optimizer_agent,
#     ],
#     # instruction="You are a travel planner agent. Help the user plan their trip.",
#     # tools=[get_weather, get_current_time],
# )