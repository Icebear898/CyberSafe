import { useEffect, useRef, useState, useCallback } from 'react';
import { apiClient } from '@/lib/api';

export interface Message {
  id: number;
  sender_id: number;
  receiver_id: number;
  content: string;
  content_filtered?: string;
  message_type: string;
  is_flagged: boolean;
  severity_score?: string;
  created_at: string;
}

export interface WebSocketMessage {
  type: string;
  id?: number;
  sender_id?: number;
  sender_username?: string;
  receiver_id?: number;
  content?: string;
  content_original?: string;
  is_flagged?: boolean;
  created_at?: string;
  message?: string;
  severity?: string;
  user_id?: number;
  username?: string;
  is_typing?: boolean;
  message_id?: number;
  message_type?: string;
  is_blocked?: boolean;
}

export const useWebSocket = (token: string | null) => {
  const [socket, setSocket] = useState<WebSocket | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [messages, setMessages] = useState<WebSocketMessage[]>([]);
  const [typingUsers, setTypingUsers] = useState<Set<number>>(new Set());
  const reconnectTimeoutRef = useRef<NodeJS.Timeout>();
  const socketRef = useRef<WebSocket | null>(null);

  const connect = useCallback(() => {
    if (!token) return;

    // Close existing connection if any
    if (socketRef.current) {
      if (socketRef.current.readyState === WebSocket.OPEN || socketRef.current.readyState === WebSocket.CONNECTING) {
        return; // Already connected or connecting
      }
    }

    const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';
    // Ensure we strip /api/v1 correctly to get the base host
    const baseUrl = apiUrl.replace('/api/v1', '');
    const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    // If baseUrl starts with http, replace protocol, otherwise assume it's just host
    const wsHost = baseUrl.replace(/^http[s]?:/, wsProtocol);

    const wsUrl = `${wsHost}/api/v1/ws/chat/${token}`;
    console.log('Connecting to WebSocket:', wsUrl);

    const ws = new WebSocket(wsUrl);
    socketRef.current = ws;

    ws.onopen = () => {
      console.log('WebSocket connected');
      setIsConnected(true);
      setSocket(ws);
    };

    ws.onmessage = (event) => {
      try {
        const data: WebSocketMessage = JSON.parse(event.data);

        if (data.type === 'message') {
          setMessages((prev) => [...prev, data]);
        } else if (data.type === 'cyberbot_warning') {
          // Handle CyberBOT warning messages
          console.log('CyberBOT warning received:', data);
          setMessages((prev) => [...prev, data]);
        } else if (data.type === 'message_sent') {
          // Handle sent confirmation - could update local message state to "sent"
          console.log('Message sent confirmed', data);
        } else if (data.type === 'typing') {
          if (data.is_typing) {
            setTypingUsers((prev) => new Set(prev).add(data.user_id!));
          } else {
            setTypingUsers((prev) => {
              const newSet = new Set(prev);
              newSet.delete(data.user_id!);
              return newSet;
            });
          }
        } else if (data.type === 'warning') {
          // Show warning notification
          console.warn('Warning:', data.message);
          // You might want to expose this to the UI
        } else if (data.type === 'error') {
          console.error('WebSocket error message:', data.message);
        }
      } catch (error) {
        console.error('Error parsing WebSocket message:', error);
      }
    };

    ws.onerror = (error) => {
      console.error('WebSocket connection error:', error);
      setIsConnected(false);
    };

    ws.onclose = (event) => {
      console.log('WebSocket disconnected', event.code, event.reason);
      setIsConnected(false);
      setSocket(null);
      socketRef.current = null;

      // Attempt to reconnect after 3 seconds if not closed cleanly
      if (event.code !== 1000 && event.code !== 1001) {
        reconnectTimeoutRef.current = setTimeout(() => {
          if (token) {
            console.log('Attempting to reconnect...');
            connect();
          }
        }, 3000);
      }
    };

    return ws;
  }, [token]);

  useEffect(() => {
    connect();

    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      if (socketRef.current) {
        socketRef.current.close();
      }
    };
  }, [connect]);

  const sendMessage = useCallback((receiverId: number, content: string, messageType: string = 'text') => {
    if (socket && socket.readyState === WebSocket.OPEN) {
      socket.send(JSON.stringify({
        type: 'message',
        receiver_id: receiverId,
        content,
        message_type: messageType,
      }));
    } else {
      console.error('WebSocket is not connected. Cannot send message.');
    }
  }, [socket]);

  const sendTyping = useCallback((receiverId: number, isTyping: boolean) => {
    if (socket && socket.readyState === WebSocket.OPEN) {
      socket.send(JSON.stringify({
        type: 'typing',
        receiver_id: receiverId,
        is_typing: isTyping,
      }));
    }
  }, [socket]);

  return {
    socket,
    isConnected,
    messages,
    typingUsers,
    sendMessage,
    sendTyping,
  };
};

