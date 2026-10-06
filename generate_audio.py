import asyncio
import os
import edge_tts

SCENES = [
    {
        "id": "scene1",
        "text": "Welcome to the demonstration of the Zizzet AI Lead Recovery Engine, built for the AI Backend Developer screening task. Businesses lose significant revenue when interested leads stop responding. This engine turns stalled conversations into structured recovery recommendations with personalized outreach, multi-tenant isolation, and resilient background processing."
    },
    {
        "id": "scene2",
        "text": "Here is our repository structure. We designed a clean, modular architecture in Python and FastAPI. It features database models with composite keys for tenant isolation, Pydantic schemas for structured output validation, a pluggable LLM abstraction supporting OpenAI, Gemini, Ollama, and deterministic mock providers, along with background worker queues."
    },
    {
        "id": "scene3",
        "text": "The API provides full interactive Swagger documentation. The four required endpoints are available: lead analysis, retrieving stored analysis, generating or sending follow-ups via mock WhatsApp, and receiving asynchronous webhook events with background processing."
    },
    {
        "id": "scene4",
        "text": "Let's examine a successful analysis request. When a customer inquires about CRM pricing for twenty-five users, the engine scores the lead at eighty-six, classifies the priority as high, and produces a hyper-personalized WhatsApp message ready for sales dispatch."
    },
    {
        "id": "scene5",
        "text": "Reliability and safety are critical. In Case D, when a customer texts STOP, our engine immediately flags do not contact as true, nulls any follow-up, and blocks outbound dispatch. Furthermore, strict multi-tenancy ensures Tenant B can never access or modify Tenant A's lead data."
    },
    {
        "id": "scene6",
        "text": "For webhook ingestion, the system provides asynchronous queue processing with strict idempotency. When the same event is submitted twice, the engine detects the duplicate hash, avoids re-processing, and returns the existing job status."
    },
    {
        "id": "scene7",
        "text": "Finally, our automated test suite validates all twenty test cases across core APIs, evaluation scenarios A through E, multi-tenancy, and error handling. The service is containerized and production ready."
    }
]

VOICE = "en-US-ChristopherNeural"

async def generate_all_audio():
    os.makedirs("video_assets/audio", exist_ok=True)
    for scene in SCENES:
        out_path = f"video_assets/audio/{scene['id']}.mp3"
        print(f"Generating audio for {scene['id']}...")
        communicate = edge_tts.Communicate(scene["text"], VOICE, rate="+3%")
        await communicate.save(out_path)
        print(f"Saved {out_path}")

if __name__ == "__main__":
    asyncio.run(generate_all_audio())
