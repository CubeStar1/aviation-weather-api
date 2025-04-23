import google.generativeai as genai
import os
import json

def configure_gemini(api_key):
    """Configure the Gemini model with the provided API key"""
    genai.configure(api_key=api_key)

def generate_weather_summary(briefing_data):
    """
    Generate a natural language summary of weather conditions using Gemini.
    
    Args:
        briefing_data (dict): The flight briefing data containing METAR, PIREP, and SIGMET info
        
    Returns:
        str: A natural language summary of the weather conditions
    """
    # Extract relevant data
    flight_plan = briefing_data.get('flight_plan', '')
    metar_data = briefing_data.get('metar', {})
    pirep_data = briefing_data.get('pireps', {})
    sigmet_data = briefing_data.get('airsigmets', [])
    
    # Format input data for the prompt
    input_data = []
    
    # Add flight plan info
    input_data.append("### Input data:")
    input_data.append(f"Flight plan: {flight_plan}")
    
    # Add METAR summaries
    input_data.append("\n### METAR Summary:")
    for airport, data in metar_data.items():
        input_data.append(f"\nAirport {airport}:")
        if data.get('general'):
            input_data.append(f"General: {data['general']}")
        if data.get('cloud'):
            input_data.append(f"Cloud condition: {data['cloud']}")
        if data.get('remarks'):
            input_data.append(f"Remarks: {'; '.join(data['remarks'])}")
            
    # Add PIREP summaries
    input_data.append("\n### PIREP Summary:")
    for airport, data in pirep_data.items():
        if data.get('status'):
            input_data.append(f"\n{data['status']}")
            
    # Add SIGMET summaries
    input_data.append("\n### SIGMET Summary:")
    for sigmet in sigmet_data:
        if sigmet.get('simplified_summary'):
            input_data.append(f"\n{sigmet['simplified_summary']}")
            
    # Create the prompt template parts
    prompt_prefix = "You are an aviation weather assistant. Based on the provided weather observations and reports, write a pre-flight briefing for the route"
    prompt_instructions = """### Output Instructions:
- Your summary should be in natural language
- Instead of displaying the numerical data as-is or spelling out numbers (like 9 as "nine"), describe them qualitatively (e.g., "light westerly winds")
- Each airport should have its own paragraph
- VFR is based on cloud condition and altitude: if flying altitude > 18,000 ft, VFR is not permitted
- Surface readings are irrelevant for flyover airports; only their cloud condition matters
- For PIREPs: mention number of reported incidents as low/medium/high to reflect likelihood of in-flight issues
- Conclude with info on **convective SIGMETs** and their impact"""

    # Combine all parts into final prompt
    prompt = f"{prompt_prefix} {flight_plan}.\n\n"
    prompt += "\n".join(input_data)
    prompt += f"\n\n{prompt_instructions}"

    try:
        model = genai.GenerativeModel("gemini-2.5-pro-exp-03-25")
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Error generating AI summary: {str(e)}" 