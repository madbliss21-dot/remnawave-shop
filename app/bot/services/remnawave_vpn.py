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
                # Use telegram ID as username if available, otherwise use vpn_id
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
            logger.error(f"Error retrieving client data for {user.tg_id}: {e}")
            return None

    async def get_key(self, user: User) -> str | None:
        """Get subscription key for user"""
        try:
            async with await self._get_api_client() as api:
                username = str(user.tg_id)
                client = await api.get_user_by_username(username)
                
                if not client:
                    logger.debug(f"Client {user.tg_id} not found for key retrieval.")
                    return None

                # Build subscription URL - the endpoint returns config, not URL, so we build URL
                base_url = self.config.remnavave.API_URL.rstrip('/')
                key = f"{base_url}/api/sub/{client.short_uuid}/singbox"
                
                logger.debug(f"Built subscription URL for {user.tg_id}: {key}.")
                return key

        except Exception as e:
            logger.error(f"Failed to get key for {user.tg_id}: {e}")
            return None

    async def create_client(
        self,
        user: User,
        devices: int,
        duration: int,
        enable: bool = True,
        traffic_limit_gb: int = 0,
        tag: str | None = None,
    ) -> bool:
        """Create new client on Remnawave"""
        logger.info(f"Creating new client {user.tg_id} | {devices} devices {duration} days.")

        try:
            async with await self._get_api_client() as api:
                username = str(user.tg_id)
                expire_at = datetime.now() + timedelta(days=duration)
                traffic_limit_bytes = traffic_limit_gb * 1024 * 1024 * 1024 if traffic_limit_gb > 0 else 0
                
                status = "ACTIVE" if enable else "DISABLED"
                
                client = await api.create_user(
                    username=username,
                    expire_at=expire_at,
                    status=status,
                    traffic_limit_bytes=traffic_limit_bytes,
                    telegram_id=user.tg_id,
                    tag=tag,
                    hwid_device_limit=devices,
                    description=f"Created by bot for user {user.tg_id}"
                )

                if client:
                    # Update user with short_uuid for easy access
                    async with self.session() as session:
                        await User.update(
                            session=session,
                            tg_id=user.tg_id,
                            vpn_id=client.short_uuid
                        )
                    logger.info(f"Successfully created client for {user.tg_id}")
                    return True
                else:
                    logger.error(f"Failed to create client for {user.tg_id}")
                    return False

        except Exception as e:
            logger.error(f"Error creating client for {user.tg_id}: {e}")
            return False

    async def update_client(
        self,
        user: User,
        devices: int | None = None,
        duration: int | None = None,
        replace_devices: bool = False,
        replace_duration: bool = False,
        enable: bool = True,
        traffic_limit_gb: int | None = None,
    ) -> bool:
        """Update existing client on Remnawave"""
        logger.info(f"Updating client {user.tg_id}.")

        try:
            async with await self._get_api_client() as api:
                username = str(user.tg_id)
                client = await api.get_user_by_username(username)

                if not client:
                    logger.error(f"Client {user.tg_id} not found for update.")
                    return False

                update_data = {}

                # Handle device limit update
                if devices is not None:
                    if replace_devices:
                        update_data["hwid_device_limit"] = devices
                    else:
                        update_data["hwid_device_limit"] = client.hwid_device_limit + devices

                # Handle expiration time update
                if duration is not None:
                    if replace_duration:
                        new_expire_at = datetime.now() + timedelta(days=duration)
                    else:
                        # Extend from current expiry time or now, whichever is later
                        current_expiry = client.expire_at
                        base_time = max(current_expiry, datetime.now())
                        new_expire_at = base_time + timedelta(days=duration)
                    
                    update_data["expire_at"] = new_expire_at

                # Handle traffic limit
                if traffic_limit_gb is not None:
                    traffic_limit_bytes = traffic_limit_gb * 1024 * 1024 * 1024 if traffic_limit_gb > 0 else 0
                    update_data["traffic_limit_bytes"] = traffic_limit_bytes

                # Handle status
                status = "ACTIVE" if enable else "DISABLED"
                if status != client.status:
                    update_data["status"] = status

                if update_data:
                    updated_client = await api.update_user(uuid=client.uuid, **update_data)
                    if updated_client:
                        logger.info(f"Client {user.tg_id} updated successfully.")
                        return True
                    else:
                        logger.error(f"Failed to update client {user.tg_id}")
                        return False
                else:
                    logger.info(f"No updates needed for client {user.tg_id}")
                    return True

        except Exception as e:
            logger.error(f"Error updating client {user.tg_id}: {e}")
            return False

    async def create_subscription(self, user: User, devices: int, duration: int) -> bool:
        """Create subscription if client doesn't exist"""
        if not await self.is_client_exists(user):
            return await self.create_client(user=user, devices=devices, duration=duration)
        return False

    async def extend_subscription(self, user: User, devices: int, duration: int) -> bool:
        """Extend existing subscription"""
        return await self.update_client(
            user=user,
            devices=0,  # Don't change devices for extension
            duration=duration,
            replace_devices=False,
            replace_duration=False,
        )

    async def change_subscription(self, user: User, devices: int, duration: int) -> bool:
        """Change subscription (replace current settings)"""
        if await self.is_client_exists(user):
            return await self.update_client(
                user=user,
                devices=devices,
                duration=duration,
                replace_devices=True,
                replace_duration=True,
            )
        return False

    async def process_bonus_days(self, user: User, duration: int, devices: int) -> bool:
        """Process bonus days for user"""
        client_exists = await self.is_client_exists(user)
        
        if client_exists:
            # Extend existing subscription
            updated = await self.update_client(
                user=user, 
                devices=0,  # Don't change device count for bonus
                duration=duration,
                replace_devices=False,
                replace_duration=False
            )
            if updated:
                logger.info(f"Extended client {user.tg_id} with additional {duration} days.")
                return True
        else:
            # Create new subscription
            created = await self.create_client(
                user=user, 
                devices=devices, 
                duration=duration
            )
            if created:
                logger.info(f"Created client {user.tg_id} with {duration} days.")
                return True

        return False

    async def activate_promocode(self, user: User, promocode: Promocode) -> bool:
        """Activate promocode for user"""
        # Mark promocode as activated in database
        async with self.session() as session:
            activated = await Promocode.set_activated(
                session=session,
                code=promocode.code,
                user_id=user.tg_id,
            )

        if not activated:
            logger.error(f"Failed to activate promocode {promocode.code} for user {user.tg_id}.")
            return False

        logger.info(f"Begun applying promocode ({promocode.code}) to a client {user.tg_id}.")
        success = await self.process_bonus_days(
            user,
            duration=promocode.duration,
            devices=self.config.shop.BONUS_DEVICES_COUNT,
        )

        if success:
            return True

        # Rollback promocode activation if VPN creation failed
        async with self.session() as session:
            await Promocode.set_deactivated(session=session, code=promocode.code)

        logger.warning(f"Promocode {promocode.code} not activated due to failure.")
        return False

    async def reset_user_traffic(self, user: User) -> bool:
        """Reset user traffic"""
        try:
            async with await self._get_api_client() as api:
                username = str(user.tg_id)
                client = await api.get_user_by_username(username)

                if not client:
                    logger.error(f"Client {user.tg_id} not found for traffic reset.")
                    return False

                success = await api.reset_user_traffic(client.uuid)
                if success:
                    logger.info(f"Successfully reset traffic for user {user.tg_id}")
                    return True
                else:
                    logger.error(f"Failed to reset traffic for user {user.tg_id}")
                    return False

        except Exception as e:
            logger.error(f"Error resetting traffic for {user.tg_id}: {e}")
            return False

    async def enable_user(self, user: User) -> bool:
        """Enable user"""
        try:
            async with await self._get_api_client() as api:
                username = str(user.tg_id)
                client = await api.get_user_by_username(username)

                if not client:
                    logger.error(f"Client {user.tg_id} not found for enabling.")
                    return False

                success = await api.enable_user(client.uuid)
                if success:
                    logger.info(f"Successfully enabled user {user.tg_id}")
                    return True
                else:
                    logger.error(f"Failed to enable user {user.tg_id}")
                    return False

        except Exception as e:
            logger.error(f"Error enabling user {user.tg_id}: {e}")
            return False

    async def disable_user(self, user: User) -> bool:
        """Disable user"""
        try:
            async with await self._get_api_client() as api:
                username = str(user.tg_id)
                client = await api.get_user_by_username(username)

                if not client:
                    logger.error(f"Client {user.tg_id} not found for disabling.")
                    return False

                success = await api.disable_user(client.uuid)
                if success:
                    logger.info(f"Successfully disabled user {user.tg_id}")
                    return True
                else:
                    logger.error(f"Failed to disable user {user.tg_id}")
                    return False

        except Exception as e:
            logger.error(f"Error disabling user {user.tg_id}: {e}")
            return False

    async def get_limit_ip(self, user: User, client: RemnavaveUser = None) -> int | None:
        """Get device limit for user (compatibility method)"""
        try:
            if not client:
                client = await self.is_client_exists(user)
            
            if not client:
                logger.debug(f"Client {user.tg_id} not found for limit IP retrieval.")
                return None
                
            return client.hwid_device_limit
            
        except Exception as e:
            logger.error(f"Error getting limit IP for {user.tg_id}: {e}")
            return None

    async def delete_client(self, user: User) -> bool:
        """Delete client (compatibility method)"""
        try:
            async with await self._get_api_client() as api:
                username = str(user.tg_id)
                client = await api.get_user_by_username(username)

                if not client:
                    logger.debug(f"Client {user.tg_id} not found for deletion.")
                    return True  # Already doesn't exist

                success = await api.delete_user(client.uuid)
                if success:
                    logger.info(f"Successfully deleted client {user.tg_id}")
                    # Clear server_id and vpn_id from user
                    async with self.session() as session:
                        await User.update(
                            session=session,
                            tg_id=user.tg_id,
                            server_id=None,
                            vpn_id=None
                        )
                    return True
                else:
                    logger.error(f"Failed to delete client {user.tg_id}")
                    return False

        except Exception as e:
            logger.error(f"Error deleting client {user.tg_id}: {e}")
            return False

    async def revoke_client(self, user: User) -> bool:
        """Revoke client subscription (disable user)"""
        return await self.disable_user(user)