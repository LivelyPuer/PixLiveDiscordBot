import asyncio
import logging
from typing import Callable, List, Optional
import aiohttp
from datetime import datetime, timedelta


logger = logging.getLogger(__name__)


class DeviantArtService:
    """Polls DeviantArt API v1 for user gallery deviations."""

    API_BASE = "https://www.deviantart.com/api/v1/oauth2"
    TOKEN_URL = "https://www.deviantart.com/oauth2/token"

    def __init__(
        self,
        username: str,
        client_id: str,
        client_secret: str,
        poll_interval: int = 60,
    ):
        self.username = username
        self.client_id = client_id
        self.client_secret = client_secret
        self.poll_interval = poll_interval
        self._running = False
        self._access_token: Optional[str] = None
        self._token_expire_time: Optional[datetime] = None

    async def _get_access_token(self, session: aiohttp.ClientSession) -> str:
        """Get or refresh OAuth2 client credentials access token."""
        now = datetime.utcnow()
        if self._access_token and self._token_expire_time and now < self._token_expire_time:
            return self._access_token

        async with session.post(
            self.TOKEN_URL,
            data={
                "grant_type": "client_credentials",
                "client_id": self.client_id,
                "client_secret": self.client_secret,
            },
        ) as resp:
            if resp.status != 200:
                raise Exception(f"Failed to get access token: {resp.status}")
            data = await resp.json()
            self._access_token = data["access_token"]
            # set expiry time to 55 minutes (token expires in 1 hour)
            self._token_expire_time = now + timedelta(seconds=data["expires_in"] - 300)
            return self._access_token

    async def fetch_gallery(
        self, session: aiohttp.ClientSession, access_token: str
    ) -> dict:
        """Fetch user gallery deviations from API."""
        headers = {"Authorization": f"Bearer {access_token}"}
        params = {"username": self.username, "limit": 24}
        async with session.get(
            f"{self.API_BASE}/gallery/all", headers=headers, params=params
        ) as resp:
            if resp.status != 200:
                raise Exception(f"Failed to fetch gallery: {resp.status}")
            return await resp.json()

    async def poll_once(self, last_timestamp: Optional[str]) -> List[dict]:
        """Poll gallery and return new deviations since last_timestamp."""
        async with aiohttp.ClientSession() as session:
            token = await self._get_access_token(session)
            data = await self.fetch_gallery(session, token)

        results = data.get("results", [])
        new_entries = []

        for deviation in results:
            # Extract unix timestamp from published_time or use published timestamp
            pub_time = deviation.get("published_time") or deviation.get("date")
            if pub_time and last_timestamp:
                if pub_time <= last_timestamp:
                    break
            new_entries.append(deviation)

        return new_entries

    async def start(self, state_getter, state_setter, poll_callback):
        """Start polling loop for gallery updates."""
        self._running = True
        logger.info(f"Starting DeviantArt service for user: {self.username}")

        while self._running:
            last_ts = await state_getter(f"{self.username}:last_timestamp")
            try:
                new_entries = await self.poll_once(last_ts)
                for entry in new_entries:
                    await poll_callback(self, entry)
                    ts = entry.get("published_time") or entry.get("date")
                    if ts:
                        await state_setter(f"{self.username}:last_timestamp", ts)
            except Exception as e:
                logger.error(
                    f"Error polling {self.username}: {e}", exc_info=True
                )
            await asyncio.sleep(self.poll_interval)

    def stop(self):
        """Stop the polling loop."""
        logger.info(f"Stopping DeviantArt service for user: {self.username}")
        self._running = False
