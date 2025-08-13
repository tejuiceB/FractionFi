import json
import uuid
from typing import Dict, List, Set
from fastapi import WebSocket, WebSocketDisconnect
from app.models.models import User
import logging

logger = logging.getLogger(__name__)

class ConnectionManager:
    def __init__(self):
        # Store active connections by user ID
        self.active_connections: Dict[str, WebSocket] = {}
        # Store room subscriptions (e.g., bond-specific rooms)
        self.rooms: Dict[str, Set[str]] = {}
        # Store user sessions
        self.user_sessions: Dict[str, str] = {}  # websocket_id -> user_id
    
    async def connect(self, websocket: WebSocket, user_id: str = None):
        """Accept a WebSocket connection"""
        await websocket.accept()
        connection_id = str(uuid.uuid4())
        self.active_connections[connection_id] = websocket
        
        if user_id:
            self.user_sessions[connection_id] = user_id
        
        logger.info(f"WebSocket connected: {connection_id} (user: {user_id})")
        return connection_id
    
    def disconnect(self, connection_id: str):
        """Remove a WebSocket connection"""
        if connection_id in self.active_connections:
            del self.active_connections[connection_id]
        
        if connection_id in self.user_sessions:
            del self.user_sessions[connection_id]
        
        # Remove from all rooms
        for room_name in list(self.rooms.keys()):
            if connection_id in self.rooms[room_name]:
                self.rooms[room_name].remove(connection_id)
                if not self.rooms[room_name]:
                    del self.rooms[room_name]
        
        logger.info(f"WebSocket disconnected: {connection_id}")
    
    async def send_personal_message(self, message: dict, connection_id: str):
        """Send a message to a specific connection"""
        if connection_id in self.active_connections:
            try:
                await self.active_connections[connection_id].send_text(json.dumps(message))
            except Exception as e:
                logger.error(f"Error sending message to {connection_id}: {e}")
                self.disconnect(connection_id)
    
    async def broadcast_to_room(self, room_name: str, message: dict):
        """Broadcast a message to all connections in a room"""
        if room_name in self.rooms:
            disconnected_connections = []
            
            for connection_id in self.rooms[room_name].copy():
                try:
                    await self.send_personal_message(message, connection_id)
                except Exception as e:
                    logger.error(f"Error broadcasting to {connection_id}: {e}")
                    disconnected_connections.append(connection_id)
            
            # Clean up disconnected connections
            for connection_id in disconnected_connections:
                self.disconnect(connection_id)
    
    async def broadcast_to_user(self, user_id: str, message: dict):
        """Send a message to a specific user (across all their connections)"""
        user_connections = [
            conn_id for conn_id, uid in self.user_sessions.items() 
            if uid == str(user_id)
        ]
        
        for connection_id in user_connections:
            await self.send_personal_message(message, connection_id)
    
    def join_room(self, connection_id: str, room_name: str):
        """Add a connection to a room"""
        if room_name not in self.rooms:
            self.rooms[room_name] = set()
        
        self.rooms[room_name].add(connection_id)
        logger.info(f"Connection {connection_id} joined room {room_name}")
    
    def leave_room(self, connection_id: str, room_name: str):
        """Remove a connection from a room"""
        if room_name in self.rooms and connection_id in self.rooms[room_name]:
            self.rooms[room_name].remove(connection_id)
            
            if not self.rooms[room_name]:
                del self.rooms[room_name]
            
            logger.info(f"Connection {connection_id} left room {room_name}")
    
    async def handle_message(self, connection_id: str, message_data: dict):
        """Handle incoming WebSocket messages"""
        message_type = message_data.get("type")
        
        if message_type == "join_room":
            room_name = message_data.get("room")
            if room_name:
                self.join_room(connection_id, room_name)
                await self.send_personal_message({
                    "type": "room_joined",
                    "room": room_name
                }, connection_id)
        
        elif message_type == "leave_room":
            room_name = message_data.get("room")
            if room_name:
                self.leave_room(connection_id, room_name)
                await self.send_personal_message({
                    "type": "room_left",
                    "room": room_name
                }, connection_id)
        
        elif message_type == "ping":
            await self.send_personal_message({
                "type": "pong",
                "timestamp": message_data.get("timestamp")
            }, connection_id)
    
    def get_room_stats(self) -> dict:
        """Get statistics about active rooms and connections"""
        return {
            "total_connections": len(self.active_connections),
            "authenticated_users": len(self.user_sessions),
            "active_rooms": len(self.rooms),
            "rooms": {
                room_name: len(connections) 
                for room_name, connections in self.rooms.items()
            }
        }

# Global WebSocket manager instance
manager = ConnectionManager()
