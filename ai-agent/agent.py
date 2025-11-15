import datetime
from google.adk.agents import LlmAgent

def get_employee(city: str) -> dict:
    """Retrieves the current weather report for a specified city.
    Args:
    city (str): The name of the city for which to retrieve the weather report.
    Returns:
    dict: status and result or error msg.
    """
    if city.lower() == "new york":
        return {
        "status": "success",
        "report": (
        "The weather in New York is sunny with a temperature of 25 degrees"
        " Celsius (77 degrees Fahrenheit)."
        ),
        }
    else:
        return {
        "status": "error",
        "error_message": f"Weather information for '{city}' is not available.",
        }

root_agent = LlmAgent(
    name="AI-administrative",
    model="gemini-2.0-flash",
    description=("Agent to help with administrative tasks such as managing employee data"),
    instruction=(
        "You are an AI administrative assistant. "
    ),
    tools=[get_employee],
    )
