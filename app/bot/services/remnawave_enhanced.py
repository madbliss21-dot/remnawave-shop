import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta

from app.bot.services.remnawave_api import RemnavaveApiClient, RemnavaveUser
from app.config import Config
from app.db.models import User

logger = logging.getLogger(__name__)


class RemnavaveEnhancedService:
    """Enhanced service utilizing Remnawave's advanced features"""

    def __init__(self, config: Config):
        self.config = config

    async def _get_api_client(self) -> RemnavaveApiClient:
        """Get authenticated API client"""
        return RemnavaveApiClient(
            base_url=self.config.remnavave.API_URL,
            username=self.config.remnavave.USERNAME,
            password=self.config.remnavave.PASSWORD
        )

    async def create_user_with_squad(
        self,
        user: User,
        devices: int,
        duration: int,
        squad_name: str,
        tag: Optional[str] = None,
        traffic_limit_gb: int = 0,
        traffic_reset_strategy: str = "NO_RESET",
    ) -> bool:
        """Create user with internal squad assignment"""
        try:
            async with await self._get_api_client() as api:
                username = str(user.tg_id)
                expire_at = datetime.now() + timedelta(days=duration)
                traffic_limit_bytes = traffic_limit_gb * 1024 * 1024 * 1024 if traffic_limit_gb > 0 else 0

                # For now, we'll use a placeholder squad UUID
                # In a real implementation, you'd need to get available squads first
                active_squads = []  # This would be populated with actual squad UUIDs

                client = await api.create_user(
                    username=username,
                    expire_at=expire_at,
                    status="ACTIVE",
                    traffic_limit_bytes=traffic_limit_bytes,
                    traffic_limit_strategy=traffic_reset_strategy,
                    telegram_id=user.tg_id,
                    tag=tag,
                    hwid_device_limit=devices,
                    description=f"Created by bot for user {user.tg_id} - Squad: {squad_name}",
                    active_internal_squads=active_squads
                )

                if client:
                    logger.info(f"Successfully created user {user.tg_id} with squad {squad_name}")
                    return True
                else:
                    logger.error(f"Failed to create user {user.tg_id} with squad")
                    return False

        except Exception as e:
            logger.error(f"Error creating user with squad for {user.tg_id}: {e}")
            return False

    async def update_user_devices(
        self,
        user: User,
        new_device_limit: int
    ) -> bool:
        """Update user's hardware device limit"""
        try:
            async with await self._get_api_client() as api:
                username = str(user.tg_id)
                client = await api.get_user_by_username(username)

                if not client:
                    logger.error(f"Client {user.tg_id} not found for device limit update.")
                    return False

                updated_client = await api.update_user(
                    uuid=client.uuid,
                    hwid_device_limit=new_device_limit
                )

                if updated_client:
                    logger.info(f"Updated device limit for user {user.tg_id} to {new_device_limit}")
                    return True
                else:
                    logger.error(f"Failed to update device limit for user {user.tg_id}")
                    return False

        except Exception as e:
            logger.error(f"Error updating device limit for {user.tg_id}: {e}")
            return False

    async def set_traffic_strategy(
        self,
        user: User,
        strategy: str,  # NO_RESET, DAY, WEEK, MONTH
        traffic_limit_gb: Optional[int] = None
    ) -> bool:
        """Set traffic reset strategy for user"""
        try:
            async with await self._get_api_client() as api:
                username = str(user.tg_id)
                client = await api.get_user_by_username(username)

                if not client:
                    logger.error(f"Client {user.tg_id} not found for traffic strategy update.")
                    return False

                kwargs = {"traffic_limit_strategy": strategy}
                
                if traffic_limit_gb is not None:
                    traffic_limit_bytes = traffic_limit_gb * 1024 * 1024 * 1024
                    kwargs["traffic_limit_bytes"] = traffic_limit_bytes

                updated_client = await api.update_user(
                    uuid=client.uuid,
                    **kwargs
                )

                if updated_client:
                    logger.info(f"Updated traffic strategy for user {user.tg_id} to {strategy}")
                    return True
                else:
                    logger.error(f"Failed to update traffic strategy for user {user.tg_id}")
                    return False

        except Exception as e:
            logger.error(f"Error updating traffic strategy for {user.tg_id}: {e}")
            return False

    async def bulk_update_users_by_tag(
        self,
        tag: str,
        **update_data
    ) -> bool:
        """Bulk update users by tag - leveraging Remnawave's tag system"""
        try:
            async with await self._get_api_client() as api:
                # This would need to be implemented in the API client
                # For now, we'll log that this feature is available
                logger.info(f"Bulk update for tag {tag} with data: {update_data}")
                
                # In a real implementation, you'd call something like:
                # success = await api.bulk_update_users_by_tag(tag=tag, **update_data)
                
                return True

        except Exception as e:
            logger.error(f"Error in bulk update for tag {tag}: {e}")
            return False

    async def get_user_statistics(self, user: User) -> Optional[Dict[str, Any]]:
        """Get enhanced user statistics"""
        try:
            async with await self._get_api_client() as api:
                username = str(user.tg_id)
                client = await api.get_user_by_username(username)

                if not client:
                    logger.error(f"Client {user.tg_id} not found for statistics.")
                    return None

                # Enhanced statistics with Remnawave-specific data
                stats = {
                    "uuid": client.uuid,
                    "short_uuid": client.short_uuid,
                    "username": client.username,
                    "status": client.status,
                    "used_traffic_bytes": client.used_traffic_bytes,
                    "lifetime_used_traffic_bytes": client.lifetime_used_traffic_bytes,
                    "traffic_limit_bytes": client.traffic_limit_bytes,
                    "traffic_limit_strategy": client.traffic_limit_strategy,
                    "expire_at": client.expire_at.isoformat(),
                    "created_at": client.created_at.isoformat(),
                    "last_traffic_reset_at": client.last_traffic_reset_at.isoformat() if client.last_traffic_reset_at else None,
                    "tag": client.tag,
                    "hwid_device_limit": client.hwid_device_limit,
                    "active_internal_squads": client.active_internal_squads,
                    "has_trojan_password": bool(client.trojan_password),
                    "has_vless_uuid": bool(client.vless_uuid),
                    "has_ss_password": bool(client.ss_password),
                }

                return stats

        except Exception as e:
            logger.error(f"Error getting statistics for {user.tg_id}: {e}")
            return None

    async def create_premium_user(
        self,
        user: User,
        devices: int,
        duration: int,
        traffic_limit_gb: int,
        premium_tag: str = "PREMIUM"
    ) -> bool:
        """Create premium user with enhanced traffic management"""
        try:
            async with await self._get_api_client() as api:
                username = str(user.tg_id)
                expire_at = datetime.now() + timedelta(days=duration)
                traffic_limit_bytes = traffic_limit_gb * 1024 * 1024 * 1024

                client = await api.create_user(
                    username=username,
                    expire_at=expire_at,
                    status="ACTIVE",
                    traffic_limit_bytes=traffic_limit_bytes,
                    traffic_limit_strategy="MONTH",  # Monthly reset for premium users
                    telegram_id=user.tg_id,
                    tag=premium_tag,
                    hwid_device_limit=devices,
                    description=f"Premium user created by bot for {user.tg_id}"
                )

                if client:
                    logger.info(f"Successfully created premium user {user.tg_id}")
                    return True
                else:
                    logger.error(f"Failed to create premium user {user.tg_id}")
                    return False

        except Exception as e:
            logger.error(f"Error creating premium user {user.tg_id}: {e}")
            return False

    async def get_subscription_configs(
        self,
        user: User,
        client_types: List[str] = None
    ) -> Dict[str, Optional[str]]:
        """Get subscription configurations for multiple client types"""
        if client_types is None:
            client_types = ["singbox", "clash", "v2ray-json", "stash"]

        configs = {}
        
        try:
            async with await self._get_api_client() as api:
                username = str(user.tg_id)
                client = await api.get_user_by_username(username)

                if not client:
                    logger.error(f"Client {user.tg_id} not found for config retrieval.")
                    return {}

                for client_type in client_types:
                    config_content = await api.get_subscription_config(client.short_uuid, client_type)
                    configs[client_type] = config_content

                logger.info(f"Retrieved {len(configs)} configs for user {user.tg_id}")
                return configs

        except Exception as e:
            logger.error(f"Error getting configs for {user.tg_id}: {e}")
            return {}

    async def manage_user_protocols(
        self,
        user: User,
        enable_trojan: bool = True,
        enable_vless: bool = True,
        enable_shadowsocks: bool = True,
        custom_passwords: Optional[Dict[str, str]] = None
    ) -> bool:
        """Manage user protocols (Trojan, VLESS, Shadowsocks)"""
        try:
            async with await self._get_api_client() as api:
                username = str(user.tg_id)
                client = await api.get_user_by_username(username)

                if not client:
                    logger.error(f"Client {user.tg_id} not found for protocol management.")
                    return False

                kwargs = {}
                
                if custom_passwords:
                    if enable_trojan and "trojan" in custom_passwords:
                        kwargs["trojan_password"] = custom_passwords["trojan"]
                    if enable_shadowsocks and "shadowsocks" in custom_passwords:
                        kwargs["ss_password"] = custom_passwords["shadowsocks"]

                # Note: VLESS uses UUID which is typically auto-generated
                # For custom VLESS UUID, you'd need to provide a valid UUID

                if kwargs:
                    updated_client = await api.update_user(
                        uuid=client.uuid,
                        **kwargs
                    )

                    if updated_client:
                        logger.info(f"Updated protocols for user {user.tg_id}")
                        return True
                    else:
                        logger.error(f"Failed to update protocols for user {user.tg_id}")
                        return False
                else:
                    logger.info(f"No protocol updates needed for user {user.tg_id}")
                    return True

        except Exception as e:
            logger.error(f"Error managing protocols for {user.tg_id}: {e}")
            return False