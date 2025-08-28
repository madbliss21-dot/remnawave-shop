import logging
import httpx
from typing import Optional, Dict, Any, List
from datetime import datetime
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class RemnavaveUser:
    """User data structure for Remnawave"""
    uuid: str
    short_uuid: str
    username: str
    status: str
    used_traffic_bytes: int
    lifetime_used_traffic_bytes: int
    traffic_limit_bytes: int
    traffic_limit_strategy: str
    expire_at: datetime
    created_at: datetime
    last_traffic_reset_at: Optional[datetime]
    description: Optional[str]
    tag: Optional[str]
    telegram_id: Optional[int]
    email: Optional[str]
    hwid_device_limit: int
    trojan_password: Optional[str]
    vless_uuid: Optional[str]
    ss_password: Optional[str]
    active_internal_squads: List[str]


@dataclass
class RemnavaveNode:
    """Node data structure for Remnawave"""
    uuid: str
    name: str
    address: str
    port: Optional[int]
    is_connected: bool
    is_disabled: bool
    is_connecting: bool
    is_node_online: bool
    is_xray_running: bool
    last_status_change: Optional[datetime]
    last_status_message: Optional[str]
    xray_version: Optional[str]
    node_version: Optional[str]
    xray_uptime: str
    is_traffic_tracking_active: bool
    traffic_reset_day: Optional[int]
    traffic_limit_bytes: Optional[int]
    notify_percent: Optional[int]
    country_code: str
    consumption_multiplier: float


@dataclass
class SubscriptionInfo:
    """Subscription information"""
    short_uuid: str
    expire_at: datetime
    traffic_limit_bytes: int
    used_traffic_bytes: int
    status: str
    username: str


class RemnavaveApiClient:
    """Remnawave API client"""

    def __init__(self, base_url: str, username: str, password: str):
        self.base_url = base_url.rstrip('/')
        self.username = username
        self.password = password
        self.access_token: Optional[str] = None
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=30.0,
            verify=False  # Consider setting to True in production with proper SSL
        )

    async def __aenter__(self):
        await self.login()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()

    async def login(self) -> bool:
        """Authenticate with Remnawave API"""
        try:
            response = await self.client.post(
                "/api/auth/login",
                json={
                    "username": self.username,
                    "password": self.password
                }
            )
            response.raise_for_status()
            data = response.json()
            self.access_token = data.get("response", {}).get("accessToken")
            
            if self.access_token:
                self.client.headers.update({
                    "Authorization": f"Bearer {self.access_token}"
                })
                logger.info("Successfully authenticated with Remnawave API")
                return True
            else:
                logger.error("No access token received from login response")
                return False

        except Exception as e:
            logger.error(f"Failed to authenticate with Remnawave API: {e}")
            return False

    async def get_user_by_username(self, username: str) -> Optional[RemnavaveUser]:
        """Get user by username"""
        try:
            response = await self.client.get(f"/api/users/by-username/{username}")
            if response.status_code == 404:
                return None
            response.raise_for_status()
            
            data = response.json()["response"]
            return self._parse_user_data(data)
            
        except Exception as e:
            logger.error(f"Failed to get user {username}: {e}")
            return None

    async def get_user_by_uuid(self, uuid: str) -> Optional[RemnavaveUser]:
        """Get user by UUID"""
        try:
            response = await self.client.get(f"/api/users/{uuid}")
            if response.status_code == 404:
                return None
            response.raise_for_status()
            
            data = response.json()["response"]
            return self._parse_user_data(data)
            
        except Exception as e:
            logger.error(f"Failed to get user {uuid}: {e}")
            return None

    async def create_user(
        self,
        username: str,
        expire_at: datetime,
        status: str = "ACTIVE",
        traffic_limit_bytes: int = 0,
        traffic_limit_strategy: str = "NO_RESET",
        telegram_id: Optional[int] = None,
        tag: Optional[str] = None,
        hwid_device_limit: int = 1,
        description: Optional[str] = None,
        email: Optional[str] = None,
        trojan_password: Optional[str] = None,
        vless_uuid: Optional[str] = None,
        ss_password: Optional[str] = None,
        active_internal_squads: Optional[List[str]] = None,
        **kwargs
    ) -> Optional[RemnavaveUser]:
        """Create a new user"""
        try:
            payload = {
                "username": username,
                "expireAt": expire_at.isoformat(),
                "status": status,
                "trafficLimitBytes": traffic_limit_bytes,
                "trafficLimitStrategy": traffic_limit_strategy,
                "hwidDeviceLimit": hwid_device_limit,
            }
            
            if telegram_id:
                payload["telegramId"] = telegram_id
            if tag:
                payload["tag"] = tag
            if description:
                payload["description"] = description
            if email:
                payload["email"] = email
            if trojan_password:
                payload["trojanPassword"] = trojan_password
            if vless_uuid:
                payload["vlessUuid"] = vless_uuid
            if ss_password:
                payload["ssPassword"] = ss_password
            if active_internal_squads:
                payload["activeInternalSquads"] = active_internal_squads
                
            # Add any additional kwargs
            payload.update(kwargs)
            
            response = await self.client.post("/api/users", json=payload)
            response.raise_for_status()
            
            data = response.json()["response"]
            logger.info(f"Successfully created user {username}")
            return self._parse_user_data(data)
            
        except Exception as e:
            logger.error(f"Failed to create user {username}: {e}")
            return None

    async def update_user(
        self,
        uuid: str,
        expire_at: Optional[datetime] = None,
        traffic_limit_bytes: Optional[int] = None,
        traffic_limit_strategy: Optional[str] = None,
        status: Optional[str] = None,
        hwid_device_limit: Optional[int] = None,
        description: Optional[str] = None,
        tag: Optional[str] = None,
        telegram_id: Optional[int] = None,
        email: Optional[str] = None,
        active_internal_squads: Optional[List[str]] = None,
        **kwargs
    ) -> Optional[RemnavaveUser]:
        """Update user"""
        try:
            payload = {"uuid": uuid}
            
            if expire_at:
                payload["expireAt"] = expire_at.isoformat()
            if traffic_limit_bytes is not None:
                payload["trafficLimitBytes"] = traffic_limit_bytes
            if traffic_limit_strategy:
                payload["trafficLimitStrategy"] = traffic_limit_strategy
            if status:
                payload["status"] = status
            if hwid_device_limit is not None:
                payload["hwidDeviceLimit"] = hwid_device_limit
            if description is not None:
                payload["description"] = description
            if tag is not None:
                payload["tag"] = tag
            if telegram_id is not None:
                payload["telegramId"] = telegram_id
            if email is not None:
                payload["email"] = email
            if active_internal_squads is not None:
                payload["activeInternalSquads"] = active_internal_squads
                
            # Add any additional kwargs
            payload.update(kwargs)
            
            response = await self.client.patch("/api/users", json=payload)
            response.raise_for_status()
            
            data = response.json()["response"]
            logger.info(f"Successfully updated user {uuid}")
            return self._parse_user_data(data)
            
        except Exception as e:
            logger.error(f"Failed to update user {uuid}: {e}")
            return None

    async def delete_user(self, uuid: str) -> bool:
        """Delete user"""
        try:
            response = await self.client.delete(f"/api/users/{uuid}")
            response.raise_for_status()
            logger.info(f"Successfully deleted user {uuid}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete user {uuid}: {e}")
            return False

    async def reset_user_traffic(self, uuid: str) -> bool:
        """Reset user traffic"""
        try:
            response = await self.client.post(f"/api/users/{uuid}/actions/reset-traffic")
            response.raise_for_status()
            logger.info(f"Successfully reset traffic for user {uuid}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to reset traffic for user {uuid}: {e}")
            return False

    async def enable_user(self, uuid: str) -> bool:
        """Enable user"""
        try:
            response = await self.client.post(f"/api/users/{uuid}/actions/enable")
            response.raise_for_status()
            logger.info(f"Successfully enabled user {uuid}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to enable user {uuid}: {e}")
            return False

    async def disable_user(self, uuid: str) -> bool:
        """Disable user"""
        try:
            response = await self.client.post(f"/api/users/{uuid}/actions/disable")
            response.raise_for_status()
            logger.info(f"Successfully disabled user {uuid}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to disable user {uuid}: {e}")
            return False

    async def get_all_nodes(self) -> List[RemnavaveNode]:
        """Get all nodes"""
        try:
            response = await self.client.get("/api/nodes")
            response.raise_for_status()
            
            data = response.json()["response"]
            nodes = []
            for node_data in data:
                nodes.append(self._parse_node_data(node_data))
            
            logger.debug(f"Retrieved {len(nodes)} nodes")
            return nodes
            
        except Exception as e:
            logger.error(f"Failed to get nodes: {e}")
            return []

    async def get_subscription_info(self, short_uuid: str) -> Optional[SubscriptionInfo]:
        """Get subscription info by short UUID"""
        try:
            response = await self.client.get(f"/api/sub/{short_uuid}/info")
            response.raise_for_status()
            
            data = response.json()["response"]
            return SubscriptionInfo(
                short_uuid=data["shortUuid"],
                expire_at=datetime.fromisoformat(data["expireAt"].replace('Z', '+00:00')),
                traffic_limit_bytes=data["trafficLimitBytes"],
                used_traffic_bytes=data["usedTrafficBytes"],
                status=data["status"],
                username=data["username"]
            )
            
        except Exception as e:
            logger.error(f"Failed to get subscription info for {short_uuid}: {e}")
            return None

    async def get_subscription_config(self, short_uuid: str, client_type: str = "singbox") -> Optional[str]:
        """Get subscription configuration for specific client type"""
        try:
            response = await self.client.get(f"/api/sub/{short_uuid}/{client_type}")
            if response.status_code == 200:
                return response.text
            return None
            
        except Exception as e:
            logger.error(f"Failed to get subscription config for {short_uuid}: {e}")
            return None

    def _parse_user_data(self, data: Dict[str, Any]) -> RemnavaveUser:
        """Parse user data from API response"""
        return RemnavaveUser(
            uuid=data["uuid"],
            short_uuid=data["shortUuid"],
            username=data["username"],
            status=data["status"],
            used_traffic_bytes=data["usedTrafficBytes"],
            lifetime_used_traffic_bytes=data["lifetimeUsedTrafficBytes"],
            traffic_limit_bytes=data["trafficLimitBytes"],
            traffic_limit_strategy=data["trafficLimitStrategy"],
            expire_at=datetime.fromisoformat(data["expireAt"].replace('Z', '+00:00')),
            created_at=datetime.fromisoformat(data["createdAt"].replace('Z', '+00:00')),
            last_traffic_reset_at=datetime.fromisoformat(data["lastTrafficResetAt"].replace('Z', '+00:00')) if data.get("lastTrafficResetAt") else None,
            description=data.get("description"),
            tag=data.get("tag"),
            telegram_id=data.get("telegramId"),
            email=data.get("email"),
            hwid_device_limit=data["hwidDeviceLimit"],
            trojan_password=data.get("trojanPassword"),
            vless_uuid=data.get("vlessUuid"),
            ss_password=data.get("ssPassword"),
            active_internal_squads=data.get("activeInternalSquads", [])
        )

    def _parse_node_data(self, data: Dict[str, Any]) -> RemnavaveNode:
        """Parse node data from API response"""
        return RemnavaveNode(
            uuid=data["uuid"],
            name=data["name"],
            address=data["address"],
            port=data.get("port"),
            is_connected=data["isConnected"],
            is_disabled=data["isDisabled"],
            is_connecting=data["isConnecting"],
            is_node_online=data["isNodeOnline"],
            is_xray_running=data["isXrayRunning"],
            last_status_change=datetime.fromisoformat(data["lastStatusChange"].replace('Z', '+00:00')) if data.get("lastStatusChange") else None,
            last_status_message=data.get("lastStatusMessage"),
            xray_version=data.get("xrayVersion"),
            node_version=data.get("nodeVersion"),
            xray_uptime=data["xrayUptime"],
            is_traffic_tracking_active=data["isTrafficTrackingActive"],
            traffic_reset_day=data.get("trafficResetDay"),
            traffic_limit_bytes=data.get("trafficLimitBytes"),
            notify_percent=data.get("notifyPercent"),
            country_code=data["countryCode"],
            consumption_multiplier=data.get("consumptionMultiplier", 1.0)
        )