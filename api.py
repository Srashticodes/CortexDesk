from fastapi import FastAPI
from pydantic import BaseModel
from triage import process_ticket
import uvicorn

app = FastAPI(title="CortexDesk API", description="AI Support Triage API", version="1.0.0")

class TicketRequest(BaseModel):
    ticket_text: str

@app.post("/analyze")
async def analyze_ticket(request: TicketRequest):
    result = process_ticket(request.ticket_text)
    return result

@app.get("/health")
async def health_check():
    return {"status": "ok"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
