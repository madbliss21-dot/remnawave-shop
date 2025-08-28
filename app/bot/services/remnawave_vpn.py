from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .remnawave_server_pool import RemnavaveServerPoolService

import logging
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.bot.models import ClientData
from app.bot.services.remnawave_api import RemnavaveApiClient, RemnavaveUser
from app.bot.utils.time import (
    add_days_to_timestamp,
    days_to_timestamp,
    get_current_timestamp,
)
from app.config import Config
from app.db.models import Promocode, User

logger = logging.getLogger(__name__)


class RemnavaveVPNService:
    def __init__(
        self,
        config: Config,
        session: async_sessionmaker,
        server_pool_service: RemnavaveServerPoolService,
    ) -> None:
        self.config = config
        self.session = session
        self.server_pool_service = server_pool_service
        logger.info("Remnawave VPN Service initialized.")

    async def _get_api_client(self) -> RemnavaveApiClient:
        """Get authenticated API client"""
        return RemnavaveApiClient(
            base_url=self.config.remnavave.API_URL,
            username=self.config.remnavave.USERNAME,
            password=self.config.remnavave.PASSWORD
        )

    async def is_client_exists(self, user: User) -> RemnavaveUser | None:
        """Check if client exists on Remnawave"""
        try:
            async with await self._get_api_client() as api:
                # Try to find user by Telegram ID first
                client = await api.get_user_by_telegram_id(user.tg_id)
                
                if not client:
                    # Fallback to username search
                    username = str(user.tg_id)
                    client = await api.get_user_by_username(username)
                
                if client:
                    logger.debug(f"Client {user.tg_id} exists on Remnawave.")
                else:
                    logger.debug(f"Client {user.tg_id} not found on Remnawave.")
                
                return client
        except Exception as e:
            logger.error(f"Failed to check if client exists for {user.tg_id}: {e}")
            return None

    async def get_client_data(self, user: User) -> ClientData | None:
        """Get client data from Remnawave"""
        logger.debug(f"Starting to retrieve client data for {user.tg_id}.")

        try:
            async with await self._get_api_client() as api:
                # Try to find user by Telegram ID first
                client = await api.get_user_by_telegram_id(user.tg_id)
                
                if not client:
                    # Fallback to username search
                    username = str(user.tg_id)
                    client = await api.get_user_by_username(username)

                if not client:
                    logger.debug(f"Client {user.tg_id} not found on Remnawave.")
                    return None

                # Convert Remnawave data to ClientData format
                max_devices = client.hwid_device_limit
                traffic_total = client.traffic_limit_bytes if client.traffic_limit_bytes > 0 else -1
                traffic_used = client.used_traffic_bytes
                
                if traffic_total <= 0:
                    traffic_remaining = -1
                else:
                    traffic_remaining = max(0, traffic_total - traffic_used)

                # Convert datetime to timestamp for compatibility
                expiry_time = int(client.expire_at.timestamp())

                client_data = ClientData(
                    max_devices=max_devices,
                    traffic_total=traffic_total,
                    traffic_remaining=traffic_remaining,
                    traffic_used=traffic_used,
                    traffic_up=traffic_used // 2,  # Remnawave doesn't separate up/down
                    traffic_down=traffic_used // 2,
                    expiry_time=expiry_time,
                )
                logger.debug(f"Successfully retrieved client data for {user.tg_id}: {client_data}.")
                return client_data

        except Exception as e:
            logger.error(f"Failed to get client data for {user.tg_id}: {e}")
            return None

    async def create_client(
        self,
        user: User,
        devices: int,
        duration: int,
        traffic_limit_gb: int = 0,
        traffic_reset_strategy: str = "NO_RESET",
        tag: str | None = None,
        description: str | None = None,
    ) -> bool:
        """Create new client on Remnawave"""
        try:
            async with await self._get_api_client() as api:
                # Check if client already exists
                existing_client = await self.is_client_exists(user)
                if existing_client:
                    logger.warning(f"Client {user.tg_id} already exists on Remnawave.")
                    return False

                # Calculate expiration date
                expire_at = datetime.now() + timedelta(days=duration)
                
                # Convert traffic limit to bytes
                traffic_limit_bytes = traffic_limit_gb * 1024 * 1024 * 1024 if traffic_limit_gb > 0 else 0
                
                # Prepare description
                if not description:
                    description = f"Created by bot for user {user.tg_id}"
                    if tag:
                        description += f" - Tag: {tag}"

                # Create user on Remnawave
                client = await api.create_user(
                    username=str(user.tg_id),
                    expire_at=expire_at,
                    status="ACTIVE",
                    traffic_limit_bytes=traffic_limit_bytes,
                    traffic_limit_strategy=traffic_reset_strategy,
                    telegram_id=user.tg_id,
                    tag=tag,
                    hwid_device_limit=devices,
                    description=description
                )

                if client:
                    logger.info(f"Successfully created client {user.tg_id} on Remnawave.")
                    return True
                else:
                    logger.error(f"Failed to create client {user.tg_id} on Remnawave.")
                    return False

        except Exception as e:
            logger.error(f"Error creating client {user.tg_id} on Remnawave: {e}")
            return False

    async def update_client(
        self,
        user: User,
        devices: int | None = None,
        duration: int | None = None,
        traffic_limit_gb: int | None = None,
        traffic_reset_strategy: str | None = None,
        tag: str | None = None,
        description: str | None = None,
    ) -> bool:
        """Update existing client on Remnawave"""
        try:
            async with await self._get_api_client() as api:
                # Find existing client
                client = await self.is_client_exists(user)
                if not client:
                    logger.error(f"Client {user.tg_id} not found on Remnawave for update.")
                    return False

                # Prepare update payload
                update_data = {}
                
                if duration is not None:
                    new_expire_at = datetime.now() + timedelta(days=duration)
                    update_data["expireAt"] = new_expire_at
                
                if traffic_limit_gb is not None:
                    traffic_limit_bytes = traffic_limit_gb * 1024 * 1024 * 1024 if traffic_limit_gb > 0 else 0
                    update_data["trafficLimitBytes"] = traffic_limit_bytes
                
                if traffic_reset_strategy is not None:
                    update_data["trafficLimitStrategy"] = traffic_reset_strategy
                
                if tag is not None:
                    update_data["tag"] = tag
                
                if description is not None:
                    update_data["description"] = description
                
                if devices is not None:
                    update_data["hwidDeviceLimit"] = devices

                # Update user on Remnawave
                updated_client = await api.update_user(
                    uuid=client.uuid,
                    **update_data
                )

                if updated_client:
                    logger.info(f"Successfully updated client {user.tg_id} on Remnawave.")
                    return True
                else:
                    logger.error(f"Failed to update client {user.tg_id} on Remnawave.")
                    return False

        except Exception as e:
            logger.error(f"Error updating client {user.tg_id} on Remnawave: {e}")
            return False

    async def extend_client(
        self,
        user: User,
        days: int,
        traffic_limit_gb: int | None = None,
    ) -> bool:
        """Extend client subscription"""
        try:
            async with await self._get_api_client() as api:
                # Find existing client
                client = await self.is_client_exists(user)
                if not client:
                    logger.error(f"Client {user.tg_id} not found on Remnawave for extension.")
                    return False

                # Calculate new expiration date
                current_expire = client.expire_at
                if current_expire < datetime.now():
                    # If expired, start from now
                    new_expire_at = datetime.now() + timedelta(days=days)
                else:
                    # If active, extend from current expiration
                    new_expire_at = current_expire + timedelta(days=days)

                # Prepare update payload
                update_data = {"expireAt": new_expire_at}
                
                if traffic_limit_gb is not None:
                    traffic_limit_bytes = traffic_limit_gb * 1024 * 1024 * 1024 if traffic_limit_gb > 0 else 0
                    update_data["trafficLimitBytes"] = traffic_limit_bytes

                # Update user on Remnawave
                updated_client = await api.update_user(
                    uuid=client.uuid,
                    **update_data
                )

                if updated_client:
                    logger.info(f"Successfully extended client {user.tg_id} by {days} days on Remnawave.")
                    return True
                else:
                    logger.error(f"Failed to extend client {user.tg_id} on Remnawave.")
                    return False

        except Exception as e:
            logger.error(f"Error extending client {user.tg_id} on Remnawave: {e}")
            return False

    async def reset_client_traffic(self, user: User) -> bool:
        """Reset client traffic usage"""
        try:
            async with await self._get_api_client() as api:
                # Find existing client
                client = await self.is_client_exists(user)
                if not client:
                    logger.error(f"Client {user.tg_id} not found on Remnawave for traffic reset.")
                    return False

                # Reset traffic on Remnawave
                success = await api.reset_user_traffic(client.uuid)

                if success:
                    logger.info(f"Successfully reset traffic for client {user.tg_id} on Remnawave.")
                    return True
                else:
                    logger.error(f"Failed to reset traffic for client {user.tg_id} on Remnawave.")
                    return False

        except Exception as e:
            logger.error(f"Error resetting traffic for client {user.tg_id} on Remnawave: {e}")
            return False

    async def disable_client(self, user: User) -> bool:
        """Disable client on Remnawave"""
        try:
            async with await self._get_api_client() as api:
                # Find existing client
                client = await self.is_client_exists(user)
                if not client:
                    logger.error(f"Client {user.tg_id} not found on Remnawave for disable.")
                    return False

                # Disable user on Remnawave
                success = await api.disable_user(client.uuid)

                if success:
                    logger.info(f"Successfully disabled client {user.tg_id} on Remnawave.")
                    return True
                else:
                    logger.error(f"Failed to disable client {user.tg_id} on Remnawave.")
                    return False

        except Exception as e:
            logger.error(f"Error disabling client {user.tg_id} on Remnawave: {e}")
            return False

    async def enable_client(self, user: User) -> bool:
        """Enable client on Remnawave"""
        try:
            async with await self._get_api_client() as api:
                # Find existing client
                client = await self.is_client_exists(user)
                if not client:
                    logger.error(f"Client {user.tg_id} not found on Remnawave for enable.")
                    return False

                # Enable user on Remnawave
                success = await api.enable_user(client.uuid)

                if success:
                    logger.info(f"Successfully enabled client {user.tg_id} on Remnawave.")
                    return True
                else:
                    logger.error(f"Failed to enable client {user.tg_id} on Remnawave.")
                    return False

        except Exception as e:
            logger.error(f"Error enabling client {user.tg_id} on Remnawave: {e}")
            return False

    async def revoke_client_subscription(self, user: User) -> bool:
        """Revoke client subscription on Remnawave"""
        try:
            async with await self._get_api_client() as api:
                # Find existing client
                client = await self.is_client_exists(user)
                if not client:
                    logger.error(f"Client {user.tg_id} not found on Remnawave for revocation.")
                    return False

                # Revoke subscription on Remnawave
                success = await api.revoke_user_subscription(client.uuid)

                if success:
                    logger.info(f"Successfully revoked subscription for client {user.tg_id} on Remnawave.")
                    return True
                else:
                    logger.error(f"Failed to revoke subscription for client {user.tg_id} on Remnawave.")
                    return False

        except Exception as e:
            logger.error(f"Error revoking subscription for client {user.tg_id} on Remnawave: {e}")
            return False

    async def get_subscription_url(self, user: User, client_type: str = "singbox") -> str | None:
        """Get subscription URL for client"""
        try:
            async with await self._get_api_client() as api:
                # Find existing client
                client = await self.is_client_exists(user)
                if not client:
                    logger.error(f"Client {user.tg_id} not found on Remnawave for subscription URL.")
                    return None

                # Get subscription URL from Remnawave
                subscription_url = await api.get_subscription_url(client.short_uuid, client_type)

                if subscription_url:
                    logger.debug(f"Successfully retrieved subscription URL for client {user.tg_id}.")
                    return subscription_url
                else:
                    logger.error(f"Failed to get subscription URL for client {user.tg_id} from Remnawave.")
                    return None

        except Exception as e:
            logger.error(f"Error getting subscription URL for client {user.tg_id}: {e}")
            return None

    async def get_subscription_info(self, user: User) -> dict | None:
        """Get detailed subscription information for client"""
        try:
            async with await self._get_api_client() as api:
                # Find existing client
                client = await self.is_client_exists(user)
                if not client:
                    logger.error(f"Client {user.tg_id} not found on Remnawave for subscription info.")
                    return None

                # Get subscription info from Remnawave
                subscription_info = await api.get_subscription_info(client.short_uuid)

                if subscription_info:
                    logger.debug(f"Successfully retrieved subscription info for client {user.tg_id}.")
                    return {
                        "short_uuid": subscription_info.short_uuid,
                        "expire_at": subscription_info.expire_at.isoformat(),
                        "traffic_limit_bytes": subscription_info.traffic_limit_bytes,
                        "used_traffic_bytes": subscription_info.used_traffic_bytes,
                        "status": subscription_info.status,
                        "username": subscription_info.username
                    }
                else:
                    logger.error(f"Failed to get subscription info for client {user.tg_id} from Remnawave.")
                    return None

        except Exception as e:
            logger.error(f"Error getting subscription info for client {user.tg_id}: {e}")
            return None