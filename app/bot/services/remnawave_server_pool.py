import logging
from typing import List, Optional, Dict, Any
from datetime import datetime

from app.bot.services.remnawave_api import RemnavaveApiClient, RemnavaveNode
from app.config import Config

logger = logging.getLogger(__name__)


class RemnavaveServerPoolService:
    """Service for managing Remnawave server pool and node operations"""

    def __init__(self, config: Config):
        self.config = config
        self._nodes: List[RemnavaveNode] = []
        self._last_sync: Optional[datetime] = None
        logger.info("Remnawave Server Pool Service initialized.")

    async def _get_api_client(self) -> RemnavaveApiClient:
        """Get authenticated API client"""
        return RemnavaveApiClient(
            base_url=self.config.remnavave.API_URL,
            username=self.config.remnavave.USERNAME,
            password=self.config.remnavave.PASSWORD
        )

    async def sync_nodes(self) -> bool:
        """Sync nodes from Remnawave API"""
        try:
            async with await self._get_api_client() as api:
                nodes = await api.get_all_nodes()
                
                if nodes is not None:
                    self._nodes = nodes
                    self._last_sync = datetime.now()
                    logger.info(f"Synced {len(self._nodes)} active nodes from Remnawave")
                    
                    # Log node status summary
                    online_nodes = [n for n in self._nodes if n.is_node_online]
                    connected_nodes = [n for n in self._nodes if n.is_connected]
                    running_nodes = [n for n in self._nodes if n.is_xray_running]
                    
                    logger.info(f"Node status: {len(online_nodes)} online, {len(connected_nodes)} connected, {len(running_nodes)} running Xray")
                    return True
                else:
                    logger.error("Failed to retrieve nodes from Remnawave API")
                    return False

        except Exception as e:
            logger.error(f"Error syncing nodes: {e}")
            return False

    async def get_nodes(self, force_sync: bool = False) -> List[RemnavaveNode]:
        """Get all nodes, optionally forcing a sync"""
        if force_sync or not self._nodes or not self._last_sync:
            await self.sync_nodes()
        return self._nodes

    async def get_online_nodes(self) -> List[RemnavaveNode]:
        """Get only online nodes"""
        nodes = await self.get_nodes()
        return [n for n in nodes if n.is_node_online]

    async def get_connected_nodes(self) -> List[RemnavaveNode]:
        """Get only connected nodes"""
        nodes = await self.get_nodes()
        return [n for n in nodes if n.is_connected]

    async def get_running_nodes(self) -> List[RemnavaveNode]:
        """Get nodes with running Xray"""
        nodes = await self.get_nodes()
        return [n for n in nodes if n.is_xray_running]

    async def get_node_by_uuid(self, node_uuid: str) -> Optional[RemnavaveNode]:
        """Get specific node by UUID"""
        nodes = await self.get_nodes()
        for node in nodes:
            if node.uuid == node_uuid:
                return node
        return None

    async def get_node_by_name(self, node_name: str) -> Optional[RemnavaveNode]:
        """Get specific node by name"""
        nodes = await self.get_nodes()
        for node in nodes:
            if node.name == node_name:
                return node
        return None

    async def get_nodes_by_country(self, country_code: str) -> List[RemnavaveNode]:
        """Get nodes by country code"""
        nodes = await self.get_nodes()
        return [n for n in nodes if n.country_code.upper() == country_code.upper()]

    async def get_best_node(self, criteria: str = "latency") -> Optional[RemnavaveNode]:
        """Get the best node based on specified criteria"""
        try:
            nodes = await self.get_online_nodes()
            
            if not nodes:
                logger.warning("No online nodes available")
                return None

            if criteria == "latency":
                # For now, return first online node
                # In a real implementation, you'd measure latency to each node
                return nodes[0]
            elif criteria == "load":
                # Return node with lowest client count (if available)
                # For now, return first online node
                return nodes[0]
            elif criteria == "traffic":
                # Return node with lowest traffic usage
                # For now, return first online node
                return nodes[0]
            else:
                logger.warning(f"Unknown criteria: {criteria}, returning first online node")
                return nodes[0]

        except Exception as e:
            logger.error(f"Error getting best node: {e}")
            return None

    async def get_node_statistics(self, node_uuid: str) -> Optional[Dict[str, Any]]:
        """Get detailed statistics for a specific node"""
        try:
            node = await self.get_node_by_uuid(node_uuid)
            if not node:
                logger.warning(f"Node {node_uuid} not found")
                return None

            stats = {
                "uuid": node.uuid,
                "name": node.name,
                "address": node.address,
                "port": node.port,
                "status": {
                    "is_connected": node.is_connected,
                    "is_disabled": node.is_disabled,
                    "is_connecting": node.is_connecting,
                    "is_node_online": node.is_node_online,
                    "is_xray_running": node.is_xray_running
                },
                "versions": {
                    "xray_version": node.xray_version,
                    "node_version": node.node_version
                },
                "uptime": node.xray_uptime,
                "traffic": {
                    "is_traffic_tracking_active": node.is_traffic_tracking_active,
                    "traffic_reset_day": node.traffic_reset_day,
                    "traffic_limit_bytes": node.traffic_limit_bytes,
                    "notify_percent": node.notify_percent
                },
                "location": {
                    "country_code": node.country_code,
                    "consumption_multiplier": node.consumption_multiplier
                },
                "last_status_change": node.last_status_change.isoformat() if node.last_status_change else None,
                "last_status_message": node.last_status_message
            }

            logger.info(f"Retrieved statistics for node {node.name}")
            return stats

        except Exception as e:
            logger.error(f"Error getting node statistics for {node_uuid}: {e}")
            return None

    async def get_pool_statistics(self) -> Optional[Dict[str, Any]]:
        """Get overall pool statistics"""
        try:
            nodes = await self.get_nodes()
            
            if not nodes:
                return {
                    "total_nodes": 0,
                    "online_nodes": 0,
                    "connected_nodes": 0,
                    "running_nodes": 0,
                    "disabled_nodes": 0
                }

            total_nodes = len(nodes)
            online_nodes = len([n for n in nodes if n.is_node_online])
            connected_nodes = len([n for n in nodes if n.is_connected])
            running_nodes = len([n for n in nodes if n.is_xray_running])
            disabled_nodes = len([n for n in nodes if n.is_disabled])

            # Group by country
            countries = {}
            for node in nodes:
                country = node.country_code
                if country not in countries:
                    countries[country] = {
                        "total": 0,
                        "online": 0,
                        "connected": 0,
                        "running": 0
                    }
                
                countries[country]["total"] += 1
                if node.is_node_online:
                    countries[country]["online"] += 1
                if node.is_connected:
                    countries[country]["connected"] += 1
                if node.is_xray_running:
                    countries[country]["running"] += 1

            stats = {
                "total_nodes": total_nodes,
                "online_nodes": online_nodes,
                "connected_nodes": connected_nodes,
                "running_nodes": running_nodes,
                "disabled_nodes": disabled_nodes,
                "availability": {
                    "online_percentage": (online_nodes / total_nodes * 100) if total_nodes > 0 else 0,
                    "connected_percentage": (connected_nodes / total_nodes * 100) if total_nodes > 0 else 0,
                    "running_percentage": (running_nodes / total_nodes * 100) if total_nodes > 0 else 0
                },
                "by_country": countries,
                "last_sync": self._last_sync.isoformat() if self._last_sync else None
            }

            logger.info("Retrieved pool statistics")
            return stats

        except Exception as e:
            logger.error(f"Error getting pool statistics: {e}")
            return None

    async def check_node_health(self, node_uuid: str) -> Optional[Dict[str, Any]]:
        """Check health status of a specific node"""
        try:
            node = await self.get_node_by_uuid(node_uuid)
            if not node:
                logger.warning(f"Node {node_uuid} not found for health check")
                return None

            health_status = "healthy"
            issues = []

            # Check various health indicators
            if not node.is_node_online:
                health_status = "unhealthy"
                issues.append("Node is offline")

            if not node.is_connected:
                health_status = "warning"
                issues.append("Node is not connected")

            if not node.is_xray_running:
                health_status = "unhealthy"
                issues.append("Xray is not running")

            if node.is_disabled:
                health_status = "disabled"
                issues.append("Node is disabled")

            # Check if node has recent status changes
            if node.last_status_change:
                time_since_change = datetime.now() - node.last_status_change
                if time_since_change.total_seconds() > 3600:  # 1 hour
                    health_status = "warning"
                    issues.append("No recent status updates")

            health_info = {
                "node_uuid": node.uuid,
                "node_name": node.name,
                "health_status": health_status,
                "issues": issues,
                "checks": {
                    "is_online": node.is_node_online,
                    "is_connected": node.is_connected,
                    "is_xray_running": node.is_xray_running,
                    "is_disabled": node.is_disabled
                },
                "last_status_change": node.last_status_change.isoformat() if node.last_status_change else None,
                "last_status_message": node.last_status_message,
                "timestamp": datetime.now().isoformat()
            }

            logger.info(f"Health check completed for node {node.name}: {health_status}")
            return health_info

        except Exception as e:
            logger.error(f"Error checking node health for {node_uuid}: {e}")
            return None

    async def get_available_nodes_for_user(self, user_requirements: Dict[str, Any]) -> List[RemnavaveNode]:
        """Get available nodes based on user requirements"""
        try:
            nodes = await self.get_online_nodes()
            
            if not nodes:
                logger.warning("No online nodes available for user")
                return []

            # Filter nodes based on requirements
            available_nodes = []

            for node in nodes:
                # Check if node meets basic requirements
                if not node.is_xray_running:
                    continue

                # Check country requirements if specified
                if "country" in user_requirements:
                    if node.country_code.upper() != user_requirements["country"].upper():
                        continue

                # Check traffic requirements if specified
                if "traffic_tracking" in user_requirements:
                    if user_requirements["traffic_tracking"] and not node.is_traffic_tracking_active:
                        continue

                # Check consumption multiplier if specified
                if "max_consumption_multiplier" in user_requirements:
                    if node.consumption_multiplier > user_requirements["max_consumption_multiplier"]:
                        continue

                available_nodes.append(node)

            logger.info(f"Found {len(available_nodes)} available nodes for user requirements")
            return available_nodes

        except Exception as e:
            logger.error(f"Error getting available nodes for user: {e}")
            return []

    async def assign_server_to_user(self, user_id: int, requirements: Dict[str, Any] = None) -> Optional[RemnavaveNode]:
        """Assign a server/node to user - for Remnawave, this is less relevant since users are global"""
        try:
            # In Remnawave, users are managed globally, not per-node
            # This method is kept for compatibility but returns the best available node
            
            if requirements is None:
                requirements = {}

            available_nodes = await self.get_available_nodes_for_user(requirements)
            
            if not available_nodes:
                logger.warning(f"No available nodes for user {user_id}")
                return None

            # Select best node based on criteria
            best_node = await self.get_best_node(criteria=requirements.get("criteria", "latency"))
            
            if best_node:
                logger.info(f"Assigned node {best_node.name} to user {user_id}")
                return best_node
            else:
                logger.warning(f"Could not assign node to user {user_id}")
                return None

        except Exception as e:
            logger.error(f"Error assigning server to user {user_id}: {e}")
            return None

    async def get_connection_for_user(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get connection for user - in Remnawave, this returns the API client and best node"""
        try:
            # For Remnawave, we don't need per-node connections since it's centralized
            # This method returns connection information for compatibility
            
            best_node = await self.get_best_node()
            
            if not best_node:
                logger.warning(f"No available nodes for user {user_id}")
                return None

            connection_info = {
                "user_id": user_id,
                "node": {
                    "uuid": best_node.uuid,
                    "name": best_node.name,
                    "address": best_node.address,
                    "port": best_node.port,
                    "country": best_node.country_code
                },
                "api_info": {
                    "base_url": self.config.remnavave.API_URL,
                    "subscription_path": self.config.remnavave.SUBSCRIPTION_URL_PATH
                },
                "timestamp": datetime.now().isoformat()
            }

            logger.info(f"Retrieved connection info for user {user_id}")
            return connection_info

        except Exception as e:
            logger.error(f"Error getting connection for user {user_id}: {e}")
            return None