import httpx
import logging

logger = logging.getLogger(__name__)

async def send_webhook(url: str, payload: dict):
    """Fire a POST request to the webhook URL with task result."""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, timeout=10)
            logger.info(f"Webhook sent to {url} — status {response.status_code}")
    except Exception as e:
        logger.error(f"Webhook failed for {url}: {e}")