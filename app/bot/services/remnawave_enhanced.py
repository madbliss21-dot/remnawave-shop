import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta

from app.bot.services.remnawave_api import RemnavaveApiClient, RemnavaveUser, RemnavaveNode
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
                # Try to find user by Telegram ID first
                client = await api.get_user_by_telegram_id(user.tg_id)

                if not client:
                    # Fallback to username search
                    username = str(user.tg_id)
                    client = await api.get_user_by_username(username)

                if not client:
                    logger.error(f"Client {user.tg_id} not found for device limit update.")
                    return False

                updated_client = await api.update_user(
                    uuid=client.uuid,
                    hwidDeviceLimit=new_device_limit
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

    async def update_user_tag(
        self,
        user: User,
        new_tag: str
    ) -> bool:
        """Update user's tag"""
        try:
            async with await self._get_api_client() as api:
                # Try to find user by Telegram ID first
                client = await api.get_user_by_telegram_id(user.tg_id)

                if not client:
                    # Fallback to username search
                    username = str(user.tg_id)
                    client = await api.get_user_by_username(username)

                if not client:
                    logger.error(f"Client {user.tg_id} not found for tag update.")
                    return False

                updated_client = await api.update_user(
                    uuid=client.uuid,
                    tag=new_tag
                )

                if updated_client:
                    logger.info(f"Updated tag for user {user.tg_id} to {new_tag}")
                    return True
                else:
                    logger.error(f"Failed to update tag for user {user.tg_id}")
                    return False

        except Exception as e:
            logger.error(f"Error updating tag for {user.tg_id}: {e}")
            return False

    async def get_users_by_tag(self, tag: str) -> List[RemnavaveUser]:
        """Get all users with specific tag"""
        try:
            async with await self._get_api_client() as api:
                users = await api.get_users_by_tag(tag)
                logger.info(f"Retrieved {len(users)} users with tag {tag}")
                return users
        except Exception as e:
            logger.error(f"Error getting users by tag {tag}: {e}")
            return []

    async def get_all_users(self, size: Optional[int] = None, start: Optional[int] = None) -> List[RemnavaveUser]:
        """Get all users with pagination"""
        try:
            async with await self._get_api_client() as api:
                users = await api.get_all_users(size=size, start=start)
                logger.info(f"Retrieved {len(users)} users")
                return users
        except Exception as e:
            logger.error(f"Error getting all users: {e}")
            return []

    async def get_user_statistics(self, user: User) -> Optional[Dict[str, Any]]:
        """Get comprehensive user statistics"""
        try:
            async with await self._get_api_client() as api:
                # Try to find user by Telegram ID first
                client = await api.get_user_by_telegram_id(user.tg_id)

                if not client:
                    # Fallback to username search
                    username = str(user.tg_id)
                    client = await api.get_user_by_username(username)

                if not client:
                    logger.error(f"Client {user.tg_id} not found for statistics.")
                    return None

                # Get subscription info
                subscription_info = await api.get_subscription_info(client.short_uuid)

                stats = {
                    "uuid": client.uuid,
                    "short_uuid": client.short_uuid,
                    "username": client.username,
                    "status": client.status,
                    "traffic_used_bytes": client.used_traffic_bytes,
                    "traffic_limit_bytes": client.traffic_limit_bytes,
                    "traffic_remaining_bytes": max(0, client.traffic_limit_bytes - client.used_traffic_bytes) if client.traffic_limit_bytes > 0 else -1,
                    "lifetime_traffic_bytes": client.lifetime_used_traffic_bytes,
                    "traffic_limit_strategy": client.traffic_limit_strategy,
                    "expire_at": client.expire_at.isoformat(),
                    "created_at": client.created_at.isoformat(),
                    "last_traffic_reset_at": client.last_traffic_reset_at.isoformat() if client.last_traffic_reset_at else None,
                    "hwid_device_limit": client.hwid_device_limit,
                    "tag": client.tag,
                    "description": client.description,
                    "subscription_info": {
                        "short_uuid": subscription_info.short_uuid,
                        "expire_at": subscription_info.expire_at.isoformat(),
                        "traffic_limit_bytes": subscription_info.traffic_limit_bytes,
                        "used_traffic_bytes": subscription_info.used_traffic_bytes,
                        "status": subscription_info.status,
                        "username": subscription_info.username
                    } if subscription_info else None
                }

                logger.info(f"Retrieved statistics for user {user.tg_id}")
                return stats

        except Exception as e:
            logger.error(f"Error getting statistics for {user.tg_id}: {e}")
            return None

    async def bulk_update_users_by_tag(
        self,
        tag: str,
        updates: Dict[str, Any]
    ) -> bool:
        """Bulk update users by tag - leveraging Remnawave's tag system"""
        try:
            async with await self._get_api_client() as api:
                # Get all users with the tag
                users = await api.get_users_by_tag(tag)
                
                if not users:
                    logger.warning(f"No users found with tag {tag}")
                    return True

                success_count = 0
                for user in users:
                    try:
                        updated_user = await api.update_user(
                            uuid=user.uuid,
                            **updates
                        )
                        if updated_user:
                            success_count += 1
                        else:
                            logger.error(f"Failed to update user {user.username}")
                    except Exception as e:
                        logger.error(f"Error updating user {user.username}: {e}")

                logger.info(f"Successfully updated {success_count}/{len(users)} users with tag {tag}")
                return success_count == len(users)

        except Exception as e:
            logger.error(f"Error in bulk update for tag {tag}: {e}")
            return False

    async def get_system_statistics(self) -> Optional[Dict[str, Any]]:
        """Get system-wide statistics"""
        try:
            async with await self._get_api_client() as api:
                # Get all users
                all_users = await api.get_all_users()
                
                # Get all nodes
                all_nodes = await api.get_all_nodes()

                # Calculate statistics
                total_users = len(all_users)
                active_users = len([u for u in all_users if u.status == "ACTIVE"])
                disabled_users = len([u for u in all_users if u.status == "DISABLED"])
                expired_users = len([u for u in all_users if u.status == "EXPIRED"])
                
                total_nodes = len(all_nodes)
                online_nodes = len([n for n in all_nodes if n.is_node_online])
                connected_nodes = len([n for n in all_nodes if n.is_connected])

                # Traffic statistics
                total_traffic_used = sum(u.used_traffic_bytes for u in all_users)
                total_traffic_limit = sum(u.traffic_limit_bytes for u in all_users if u.traffic_limit_bytes > 0)

                stats = {
                    "users": {
                        "total": total_users,
                        "active": active_users,
                        "disabled": disabled_users,
                        "expired": expired_users,
                        "active_percentage": (active_users / total_users * 100) if total_users > 0 else 0
                    },
                    "nodes": {
                        "total": total_nodes,
                        "online": online_nodes,
                        "connected": connected_nodes,
                        "online_percentage": (online_nodes / total_nodes * 100) if total_nodes > 0 else 0
                    },
                    "traffic": {
                        "total_used_bytes": total_traffic_used,
                        "total_limit_bytes": total_traffic_limit,
                        "usage_percentage": (total_traffic_used / total_traffic_limit * 100) if total_traffic_limit > 0 else 0
                    }
                }

                logger.info("Retrieved system statistics")
                return stats

        except Exception as e:
            logger.error(f"Error getting system statistics: {e}")
            return None

    async def get_node_information(self, node_uuid: str) -> Optional[RemnavaveNode]:
        """Get specific node information"""
        try:
            async with await self._get_api_client() as api:
                # Get all nodes and find the specific one
                all_nodes = await api.get_all_nodes()
                
                for node in all_nodes:
                    if node.uuid == node_uuid:
                        logger.info(f"Retrieved information for node {node.name}")
                        return node
                
                logger.warning(f"Node with UUID {node_uuid} not found")
                return None

        except Exception as e:
            logger.error(f"Error getting node information for {node_uuid}: {e}")
            return None

    async def get_user_connection_info(self, user: User) -> Optional[Dict[str, Any]]:
        """Get user connection information including subscription URLs"""
        try:
            async with await self._get_api_client() as api:
                # Try to find user by Telegram ID first
                client = await api.get_user_by_telegram_id(user.tg_id)

                if not client:
                    # Fallback to username search
                    username = str(user.tg_id)
                    client = await api.get_user_by_username(username)

                if not client:
                    logger.error(f"Client {user.tg_id} not found for connection info.")
                    return None

                # Get subscription URLs for different client types
                singbox_url = await api.get_subscription_url(client.short_uuid, "singbox")
                v2ray_url = await api.get_subscription_url(client.short_uuid, "v2ray")
                clash_url = await api.get_subscription_url(client.short_uuid, "clash")

                connection_info = {
                    "username": client.username,
                    "status": client.status,
                    "expire_at": client.expire_at.isoformat(),
                    "subscription_urls": {
                        "singbox": singbox_url,
                        "v2ray": v2ray_url,
                        "clash": clash_url
                    },
                    "protocols": {
                        "trojan": client.trojan_password,
                        "vless": client.vless_uuid,
                        "shadowsocks": client.ss_password
                    },
                    "device_limit": client.hwid_device_limit
                }

                logger.info(f"Retrieved connection info for user {user.tg_id}")
                return connection_info

        except Exception as e:
            logger.error(f"Error getting connection info for {user.tg_id}: {e}")
            return None