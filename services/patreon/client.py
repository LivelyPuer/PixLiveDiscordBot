import aiohttp
import logging
from typing import Optional

logger = logging.getLogger(__name__)

class PatreonClient:
    API_BASE = "https://www.patreon.com/api/oauth2/v2"

    def __init__(self, access_token: str):
        self.access_token = access_token

    async def get_post_title(self, post_id: str) -> Optional[str]:
        if not self.access_token:
            logger.warning("Patreon access token not set, cannot fetch post title.")
            return None

        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "User-Agent": "PixLiveBot/1.0"
        }
        
        url = f"{self.API_BASE}/posts/{post_id}"
        params = {
            "fields[post]": "title"
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, params=params) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        return data.get("data", {}).get("attributes", {}).get("title")
                    else:
                        logger.error(f"Patreon API returned {resp.status} for post {post_id}")
                        try:
                            logger.error(await resp.text())
                        except:
                            pass
                        return None
        except Exception as e:
            logger.error(f"Error fetching Patreon post {post_id}: {e}")
            return None
