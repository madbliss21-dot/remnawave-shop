import logging
import httpx
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from dataclasses import dataclass
import json

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
    """Remnawave API client with improved error handling and token management"""

    def __init__(self, base_url: str, username: str, password: str):
        self.base_url = base_url.rstrip('/')
        self.username = username
        self.password = password
        self.access_token: Optional[str] = None
        self.token_expires_at: Optional[datetime] = None
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

    async def _ensure_token_valid(self) -> bool:
        """Ensure access token is valid, refresh if needed"""
        if not self.access_token:
            return await self.login()
        
        if self.token_expires_at and datetime.now() >= self.token_expires_at:
            logger.info("Access token expired, refreshing...")
            return await self.login()
        
        return True

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
            
            if response.status_code == 401:
                logger.error("Invalid credentials for Remnawave API")
                return False
            elif response.status_code == 500:
                logger.error("Server error during authentication")
                return False
                
            response.raise_for_status()
            data = response.json()
            
            # Handle both possible response formats
            if "response" in data and "accessToken" in data["response"]:
                self.access_token = data["response"]["accessToken"]
            elif "accessToken" in data:
                self.access_token = data["accessToken"]
            else:
                logger.error("No access token received from login response")
                return False
            
            # Set token expiration (assuming 24 hours if not specified)
            self.token_expires_at = datetime.now() + timedelta(hours=23)  # Refresh 1 hour before expiry
            
            self.client.headers.update({
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json"
            })
            
            logger.info("Successfully authenticated with Remnawave API")
            return True

        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error during authentication: {e.response.status_code} - {e.response.text}")
            return False
        except Exception as e:
            logger.error(f"Failed to authenticate with Remnawave API: {e}")
            return False

    async def _make_request(self, method: str, url: str, **kwargs) -> Optional[httpx.Response]:
        """Make authenticated request with automatic token refresh"""
        if not await self._ensure_token_valid():
            return None
            
        try:
            response = await self.client.request(method, url, **kwargs)
            
            # If token expired during request, try to refresh and retry once
            if response.status_code == 401:
                logger.info("Token expired during request, refreshing...")
                if await self.login():
                    response = await self.client.request(method, url, **kwargs)
                else:
                    return None
            
            return response
            
        except Exception as e:
            logger.error(f"Request failed: {method} {url} - {e}")
            return None

    async def get_user_by_username(self, username: str) -> Optional[RemnavaveUser]:
        """Get user by username"""
        try:
            response = await self._make_request("GET", f"/api/users/by-username/{username}")
            if not response:
                return None
                
            if response.status_code == 404:
                return None
            response.raise_for_status()
            
            data = response.json()
            # Handle both response formats
            user_data = data.get("response", data)
            return self._parse_user_data(user_data)
            
        except Exception as e:
            logger.error(f"Failed to get user {username}: {e}")
            return None

    async def get_user_by_uuid(self, uuid: str) -> Optional[RemnavaveUser]:
        """Get user by UUID"""
        try:
            response = await self._make_request("GET", f"/api/users/{uuid}")
            if not response:
                return None
                
            if response.status_code == 404:
                return None
            response.raise_for_status()
            
            data = response.json()
            user_data = data.get("response", data)
            return self._parse_user_data(user_data)
            
        except Exception as e:
            logger.error(f"Failed to get user {uuid}: {e}")
            return None

    async def get_user_by_short_uuid(self, short_uuid: str) -> Optional[RemnavaveUser]:
        """Get user by short UUID"""
        try:
            response = await self._make_request("GET", f"/api/users/by-short-uuid/{short_uuid}")
            if not response:
                return None
                
            if response.status_code == 404:
                return None
            response.raise_for_status()
            
            data = response.json()
            user_data = data.get("response", data)
            return self._parse_user_data(user_data)
            
        except Exception as e:
            logger.error(f"Failed to get user by short UUID {short_uuid}: {e}")
            return None

    async def get_user_by_telegram_id(self, telegram_id: int) -> Optional[RemnavaveUser]:
        """Get user by Telegram ID"""
        try:
            response = await self._make_request("GET", f"/api/users/by-telegram-id/{telegram_id}")
            if not response:
                return None
                
            if response.status_code == 404:
                return None
            response.raise_for_status()
            
            data = response.json()
            user_data = data.get("response", data)
            return self._parse_user_data(user_data)
            
        except Exception as e:
            logger.error(f"Failed to get user by Telegram ID {telegram_id}: {e}")
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
                
            # Add any additional kwargs
            payload.update(kwargs)
            
            response = await self._make_request("POST", "/api/users", json=payload)
            if not response:
                return None
                
            response.raise_for_status()
            
            data = response.json()
            user_data = data.get("response", data)
            logger.info(f"Successfully created user {username}")
            return self._parse_user_data(user_data)
            
        except Exception as e:
            logger.error(f"Failed to create user {username}: {e}")
            return None

    async def update_user(
        self,
        uuid: str,
        expire_at: Optional[datetime] = None,
        traffic_limit_bytes: Optional[int] = None,
        status: Optional[str] = None,
        **kwargs
    ) -> Optional[RemnavaveUser]:
        """Update user"""
        try:
            payload = {"uuid": uuid}
            
            if expire_at:
                payload["expireAt"] = expire_at.isoformat()
            if traffic_limit_bytes is not None:
                payload["trafficLimitBytes"] = traffic_limit_bytes
            if status:
                payload["status"] = status
                
            # Add any additional kwargs
            payload.update(kwargs)
            
            response = await self._make_request("PATCH", "/api/users", json=payload)
            if not response:
                return None
                
            response.raise_for_status()
            
            data = response.json()
            user_data = data.get("response", data)
            logger.info(f"Successfully updated user {uuid}")
            return self._parse_user_data(user_data)
            
        except Exception as e:
            logger.error(f"Failed to update user {uuid}: {e}")
            return None

    async def delete_user(self, uuid: str) -> bool:
        """Delete user"""
        try:
            response = await self._make_request("DELETE", f"/api/users/{uuid}")
            if not response:
                return False
                
            response.raise_for_status()
            logger.info(f"Successfully deleted user {uuid}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete user {uuid}: {e}")
            return False

    async def reset_user_traffic(self, uuid: str) -> bool:
        """Reset user traffic"""
        try:
            response = await self._make_request("POST", f"/api/users/{uuid}/actions/reset-traffic")
            if not response:
                return False
                
            response.raise_for_status()
            logger.info(f"Successfully reset traffic for user {uuid}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to reset traffic for user {uuid}: {e}")
            return False

    async def enable_user(self, uuid: str) -> bool:
        """Enable user"""
        try:
            response = await self._make_request("POST", f"/api/users/{uuid}/actions/enable")
            if not response:
                return False
                
            response.raise_for_status()
            logger.info(f"Successfully enabled user {uuid}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to enable user {uuid}: {e}")
            return False

    async def disable_user(self, uuid: str) -> bool:
        """Disable user"""
        try:
            response = await self._make_request("POST", f"/api/users/{uuid}/actions/disable")
            if not response:
                return False
                
            response.raise_for_status()
            logger.info(f"Successfully disabled user {uuid}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to disable user {uuid}: {e}")
            return False

    async def revoke_user_subscription(self, uuid: str) -> bool:
        """Revoke user subscription"""
        try:
            response = await self._make_request("POST", f"/api/users/{uuid}/actions/revoke")
            if not response:
                return False
                
            response.raise_for_status()
            logger.info(f"Successfully revoked subscription for user {uuid}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to revoke subscription for user {uuid}: {e}")
            return False

    async def get_all_users(self, size: Optional[int] = None, start: Optional[int] = None) -> List[RemnavaveUser]:
        """Get all users with pagination"""
        try:
            params = {}
            if size:
                params["size"] = size
            if start:
                params["start"] = start
                
            response = await self._make_request("GET", "/api/users", params=params)
            if not response:
                return []
                
            response.raise_for_status()
            
            data = response.json()
            users_data = data.get("response", data)
            
            users = []
            for user_data in users_data:
                users.append(self._parse_user_data(user_data))
            
            logger.debug(f"Retrieved {len(users)} users")
            return users
            
        except Exception as e:
            logger.error(f"Failed to get users: {e}")
            return []

    async def get_users_by_tag(self, tag: str) -> List[RemnavaveUser]:
        """Get users by tag"""
        try:
            response = await self._make_request("GET", f"/api/users/by-tag/{tag}")
            if not response:
                return []
                
            response.raise_for_status()
            
            data = response.json()
            users_data = data.get("response", data)
            
            users = []
            for user_data in users_data:
                users.append(self._parse_user_data(user_data))
            
            logger.debug(f"Retrieved {len(users)} users with tag {tag}")
            return users
            
        except Exception as e:
            logger.error(f"Failed to get users by tag {tag}: {e}")
            return []

    async def get_all_nodes(self) -> List[RemnavaveNode]:
        """Get all nodes"""
        try:
            response = await self._make_request("GET", "/api/nodes")
            if not response:
                return []
                
            response.raise_for_status()
            
            data = response.json()
            nodes_data = data.get("response", data)
            
            nodes = []
            for node_data in nodes_data:
                nodes.append(self._parse_node_data(node_data))
            
            logger.debug(f"Retrieved {len(nodes)} nodes")
            return nodes
            
        except Exception as e:
            logger.error(f"Failed to get nodes: {e}")
            return []

    async def get_subscription_info(self, short_uuid: str) -> Optional[SubscriptionInfo]:
        """Get subscription info by short UUID"""
        try:
            response = await self._make_request("GET", f"/api/sub/{short_uuid}/info")
            if not response:
                return None
                
            response.raise_for_status()
            
            data = response.json()
            sub_data = data.get("response", data)
            
            return SubscriptionInfo(
                short_uuid=sub_data["shortUuid"],
                expire_at=datetime.fromisoformat(sub_data["expireAt"].replace('Z', '+00:00')),
                traffic_limit_bytes=sub_data["trafficLimitBytes"],
                used_traffic_bytes=sub_data["usedTrafficBytes"],
                status=sub_data["status"],
                username=sub_data["username"]
            )
            
        except Exception as e:
            logger.error(f"Failed to get subscription info for {short_uuid}: {e}")
            return None

    async def get_subscription_url(self, short_uuid: str, client_type: str = "singbox") -> Optional[str]:
        """Get subscription URL for specific client type"""
        try:
            response = await self._make_request("GET", f"/api/sub/{short_uuid}/{client_type}")
            if not response:
                return None
                
            if response.status_code == 200:
                return response.text
            return None
            
        except Exception as e:
            logger.error(f"Failed to get subscription URL for {short_uuid}: {e}")
            return None

    async def get_raw_subscription(self, short_uuid: str, with_disabled_hosts: bool = False) -> Optional[Dict[str, Any]]:
        """Get raw subscription data"""
        try:
            params = {"withDisabledHosts": with_disabled_hosts}
            response = await self._make_request("GET", f"/api/sub/{short_uuid}/raw", params=params)
            if not response:
                return None
                
            response.raise_for_status()
            return response.json()
            
        except Exception as e:
            logger.error(f"Failed to get raw subscription for {short_uuid}: {e}")
            return None

    def _parse_user_data(self, data: Dict[str, Any]) -> RemnavaveUser:
        """Parse user data from API response"""
        try:
            return RemnavaveUser(
                uuid=data["uuid"],
                short_uuid=data["shortUuid"],
                username=data["username"],
                status=data["status"],
                used_traffic_bytes=data.get("usedTrafficBytes", 0),
                lifetime_used_traffic_bytes=data.get("lifetimeUsedTrafficBytes", 0),
                traffic_limit_bytes=data.get("trafficLimitBytes", 0),
                traffic_limit_strategy=data.get("trafficLimitStrategy", "NO_RESET"),
                expire_at=datetime.fromisoformat(data["expireAt"].replace('Z', '+00:00')),
                created_at=datetime.fromisoformat(data["createdAt"].replace('Z', '+00:00')),
                last_traffic_reset_at=datetime.fromisoformat(data["lastTrafficResetAt"].replace('Z', '+00:00')) if data.get("lastTrafficResetAt") else None,
                description=data.get("description"),
                tag=data.get("tag"),
                telegram_id=data.get("telegramId"),
                email=data.get("email"),
                hwid_device_limit=data.get("hwidDeviceLimit", 1),
                trojan_password=data.get("trojanPassword"),
                vless_uuid=data.get("vlessUuid"),
                ss_password=data.get("ssPassword"),
                active_internal_squads=data.get("activeInternalSquads", [])
            )
        except KeyError as e:
            logger.error(f"Missing required field in user data: {e}")
            raise
        except Exception as e:
            logger.error(f"Error parsing user data: {e}")
            raise

    def _parse_node_data(self, data: Dict[str, Any]) -> RemnavaveNode:
        """Parse node data from API response"""
        try:
            return RemnavaveNode(
                uuid=data["uuid"],
                name=data["name"],
                address=data["address"],
                port=data.get("port"),
                is_connected=data.get("isConnected", False),
                is_disabled=data.get("isDisabled", False),
                is_connecting=data.get("isConnecting", False),
                is_node_online=data.get("isNodeOnline", False),
                is_xray_running=data.get("isXrayRunning", False),
                last_status_change=datetime.fromisoformat(data["lastStatusChange"].replace('Z', '+00:00')) if data.get("lastStatusChange") else None,
                last_status_message=data.get("lastStatusMessage"),
                xray_version=data.get("xrayVersion"),
                node_version=data.get("nodeVersion"),
                xray_uptime=data.get("xrayUptime", "0s"),
                is_traffic_tracking_active=data.get("isTrafficTrackingActive", False),
                traffic_reset_day=data.get("trafficResetDay"),
                traffic_limit_bytes=data.get("trafficLimitBytes"),
                notify_percent=data.get("notifyPercent"),
                country_code=data.get("countryCode", "UNKNOWN"),
                consumption_multiplier=data.get("consumptionMultiplier", 1.0)
            )
        except KeyError as e:
            logger.error(f"Missing required field in node data: {e}")
            raise
        except Exception as e:
            logger.error(f"Error parsing node data: {e}")
            raise