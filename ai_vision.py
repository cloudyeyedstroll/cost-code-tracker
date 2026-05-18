import os
from google import genai
from pydantic import BaseModel, Field
import database

class DeliveryTicket(BaseModel):
    supplier: str = Field(description="Name of the supplier or quarry (e.g., Heidelberg Materials, Vulcan)")
    material_description: str = Field(description="Description of the material delivered (e.g., 57 Stone, Base, Aggregate, Asphalt)")
    quantity: float = Field(description="Total quantity or net weight delivered")
    unit: str = Field(description="Unit of measurement (e.g., Tons, TN, CY, Loads)")
    ticket_number: str = Field(description="Delivery ticket or scale ticket number")
    date: str = Field(description="Date of delivery in YYYY-MM-DD format")

def extract_ticket_data(image_bytes: bytes) -> DeliveryTicket:
    """
    Parses a delivery ticket image and extracts structured data using Gemini 2.5 Flash.
    """
    # Try to get API key from integration settings first
    settings = database.get_integration_settings()
    api_key = None
    if settings and settings.get('vision_ai_key'):
        api_key = settings['vision_ai_key']
    
    # Fallback to environment variable
    if not api_key:
        api_key = os.environ.get("GEMINI_API_KEY")
        
    if not api_key:
        raise ValueError("Gemini API Key is not configured. Please add it to the Connected Integrations Hub or set GEMINI_API_KEY in the environment.")

    client = genai.Client(api_key=api_key)
    
    # Prompt the model with structured output requirement
    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=[
            "Extract the details from this heavy civil material delivery ticket. Ensure numbers and units are accurate.",
            {"mime_type": "image/jpeg", "data": image_bytes}
        ],
        config={
            'response_mime_type': 'application/json',
            'response_schema': DeliveryTicket,
        },
    )
    
    return response.parsed

class SubcontractorTicket(BaseModel):
    ticket_number: str | None = Field(description="Ticket number or ID if present")
    company_name: str | None = Field(description="Name of the subcontractor company (e.g., Fraser Valley Hydrovac, MHR Trucking)")
    scope_of_work: str | None = Field(description="Brief summary of work performed")
    hours_worked: float | None = Field(description="Total hours, regular hours, or operator shift duration")

def extract_subcontractor_ticket(image_bytes: bytes) -> SubcontractorTicket:
    """
    Parses a subcontractor field sheet or trucking slip and extracts structured data using Gemini 2.5 Flash.
    """
    settings = database.get_integration_settings()
    api_key = None
    if settings and settings.get('vision_ai_key'):
        api_key = settings['vision_ai_key']
    
    if not api_key:
        api_key = os.environ.get("GEMINI_API_KEY")
        
    if not api_key:
        raise ValueError("Gemini API Key is not configured. Please add it to the Connected Integrations Hub or set GEMINI_API_KEY in the environment.")

    client = genai.Client(api_key=api_key)
    
    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=[
            "You are a civil construction billing clerk. Read this subcontractor field sheet, hydrovac ticket, or hired trucking slip. Extract the text properties precisely.",
            {"mime_type": "image/jpeg", "data": image_bytes}
        ],
        config={
            'response_mime_type': 'application/json',
            'response_schema': SubcontractorTicket,
        },
    )
    
    return response.parsed
