import { useState, useEffect, useRef } from 'react';
import {
  Alert,
  Avatar,
  Badge,
  Box,
  Button,
  CircularProgress,
  Container,
  IconButton,
  InputAdornment,
  List,
  ListItem,
  ListItemAvatar,
  ListItemButton,
  ListItemText,
  Menu,
  MenuItem,
  Paper,
  Stack,
  TextField,
  Tooltip,
  Typography,
  useMediaQuery,
  Fab,
} from '@mui/material';
import { useTheme } from '@mui/material/styles';
import { useLocation, useNavigate } from 'react-router-dom';
import SearchRoundedIcon from '@mui/icons-material/SearchRounded';
import SendRoundedIcon from '@mui/icons-material/SendRounded';
import MoreVertRoundedIcon from '@mui/icons-material/MoreVertRounded';
import PersonRoundedIcon from '@mui/icons-material/PersonRounded';
import PeopleRoundedIcon from '@mui/icons-material/PeopleRounded';
import PsychologyRoundedIcon from '@mui/icons-material/PsychologyRounded';
import LogoutRoundedIcon from '@mui/icons-material/LogoutRounded';
import AdminPanelSettingsRoundedIcon from '@mui/icons-material/AdminPanelSettingsRounded';
import PhoneRoundedIcon from '@mui/icons-material/PhoneRounded';
import VideocamRoundedIcon from '@mui/icons-material/VideocamRounded';
import InfoOutlinedIcon from '@mui/icons-material/InfoOutlined';
import AttachFileRoundedIcon from '@mui/icons-material/AttachFileRounded';
import InsertEmoticonRoundedIcon from '@mui/icons-material/InsertEmoticonRounded';
import ImageRoundedIcon from '@mui/icons-material/ImageRounded';
import ArrowBackRoundedIcon from '@mui/icons-material/ArrowBackRounded';
import { apiClient, UserSummary } from '@/lib/api';
import { useWebSocket, WebSocketMessage } from '@/hooks/useWebSocket';
import { format } from 'date-fns';
import CyberbullyingAlertDialog from '@/components/CyberbullyingAlertDialog';

interface Conversation {
  user: { id: number; username: string; avatar_url?: string; has_red_tag?: boolean };
  last_message: { id: number; content: string; created_at: string; sender_id: number };
}

interface Message {
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

const Chat = () => {
  const theme = useTheme();
  const navigate = useNavigate();
  const location = useLocation();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [selectedUserId, setSelectedUserId] = useState<number | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [message, setMessage] = useState('');
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const [currentUser, setCurrentUser] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [conversationSearch, setConversationSearch] = useState('');
  const [searchResults, setSearchResults] = useState<UserSummary[]>([]);
  const [searchLoading, setSearchLoading] = useState(false);
  const [alertDialogOpen, setAlertDialogOpen] = useState(false);
  const [flaggedMessage, setFlaggedMessage] = useState<Message | null>(null);
  const [selectedPeer, setSelectedPeer] = useState<{ id: number; username: string; avatar_url?: string | null; has_red_tag?: boolean } | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const typingTimeoutRef = useRef<NodeJS.Timeout>();
  const fileInputRef = useRef<HTMLInputElement>(null);

  const token = sessionStorage.getItem('auth_token');
  const { isConnected, sendMessage, sendTyping, messages: wsMessages } = useWebSocket(token);

  const isAdmin = currentUser?.role === 'admin';

  const filteredConversations = conversations.filter((conversation) => {
    if (!conversationSearch.trim()) return true;
    const query = conversationSearch.toLowerCase();
    return (
      conversation.user.username.toLowerCase().includes(query) ||
      conversation.last_message.content.toLowerCase().includes(query)
    );
  });

  const selectedConversation = conversations.find((c) => c.user.id === selectedUserId);
  const activePeer =
    selectedPeer ||
    (selectedConversation
      ? {
        id: selectedConversation.user.id,
        username: selectedConversation.user.username,
        avatar_url: selectedConversation.user.avatar_url,
      }
      : null);

  const handleSelectConversation = (conversation: Conversation) => {
    setSelectedUserId(conversation.user.id);
    setSelectedPeer({
      id: conversation.user.id,
      username: conversation.user.username,
      avatar_url: conversation.user.avatar_url,
    });
  };

  const handleSelectUser = (user: UserSummary) => {
    setSelectedUserId(user.id);
    setSelectedPeer({
      id: user.id,
      username: user.username,
      avatar_url: user.avatar_url,
    });
    setConversationSearch('');
    setSearchResults([]);
  };

  useEffect(() => {
    loadUserAndConversations();
  }, []);

  useEffect(() => {
    if (selectedUserId !== null) {
      loadMessages(selectedUserId);
    }
  }, [selectedUserId]);

  useEffect(() => {
    const state = location.state as
      | {
        user?: { id: number; username: string; avatar_url?: string | null };
        userId?: number;
      }
      | undefined;
    if (state?.user) {
      setSelectedUserId(state.user.id);
      setSelectedPeer({
        id: state.user.id,
        username: state.user.username,
        avatar_url: state.user.avatar_url,
      });
    } else if (state?.userId) {
      setSelectedUserId(state.userId);
    }
  }, [location]);

  useEffect(() => {
    if (!isMobile && selectedUserId === null && conversations.length > 0) {
      setSelectedUserId(conversations[0].user.id);
    }
    if (selectedUserId !== null && conversations.length > 0) {
      const existing = conversations.find((c) => c.user.id === selectedUserId);
      if (existing) {
        setSelectedPeer({
          id: existing.user.id,
          username: existing.user.username,
          avatar_url: existing.user.avatar_url,
          has_red_tag: existing.user.has_red_tag,
        });
      }
    }
  }, [conversations, selectedUserId, isMobile]);

  useEffect(() => {
    const query = conversationSearch.trim();
    if (query.length < 2) {
      setSearchResults([]);
      setSearchLoading(false);
      return;
    }

    let active = true;
    setSearchLoading(true);
    apiClient
      .searchUsers(query)
      .then((users) => {
        if (active) {
          setSearchResults(users);
        }
      })
      .catch(() => {
        if (active) {
          setSearchResults([]);
        }
      })
      .finally(() => {
        if (active) {
          setSearchLoading(false);
        }
      });

    return () => {
      active = false;
    };
  }, [conversationSearch]);

  useEffect(() => {
    wsMessages.forEach((wsMsg: WebSocketMessage) => {
      // Handle regular messages
      if (wsMsg.type === 'message' && wsMsg.sender_id === selectedUserId) {
        setMessages((prev) => [
          ...prev,
          {
            id: wsMsg.id!,
            sender_id: wsMsg.sender_id!,
            receiver_id: selectedUserId,
            content: wsMsg.content!,
            content_filtered: (wsMsg as any).content_filtered || wsMsg.content,
            message_type: wsMsg.message_type || 'text',
            is_flagged: wsMsg.is_flagged || false,
            severity_score: (wsMsg as any).severity_score,
            created_at: wsMsg.created_at!,
          },
        ]);

        // Check if message is flagged and from the other user
        if (wsMsg.is_flagged && wsMsg.sender_id !== currentUser?.id) {
          const flaggedMsg = {
            id: wsMsg.id!,
            sender_id: wsMsg.sender_id!,
            receiver_id: selectedUserId,
            content: wsMsg.content!,
            content_filtered: (wsMsg as any).content_filtered || wsMsg.content,
            message_type: wsMsg.message_type || 'text',
            is_flagged: true,
            severity_score: (wsMsg as any).severity_score,
            created_at: wsMsg.created_at!,
          };
          setFlaggedMessage(flaggedMsg);
          setAlertDialogOpen(true);
        }

        scrollToBottom();
      }

      // Handle CyberBOT warning messages
      if (wsMsg.type === 'cyberbot_warning' && wsMsg.sender_id === 0) {
        // Only add to messages if we're viewing the CyberBOT conversation
        if (selectedUserId === 0) {
          setMessages((prev) => [
            ...prev,
            {
              id: wsMsg.id!,
              sender_id: 0, // CyberBOT ID
              receiver_id: currentUser?.id || 0,
              content: wsMsg.content!,
              content_filtered: wsMsg.content!,
              message_type: 'system_warning',
              is_flagged: false,
              severity_score: 'info',
              created_at: wsMsg.created_at!,
            },
          ]);
          scrollToBottom();
        }

        // Always reload conversations to show CyberBOT chat in the list
        loadUserAndConversations();
      }
    });
  }, [wsMessages, selectedUserId, currentUser]);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const loadUserAndConversations = async () => {
    try {
      const user = await apiClient.getCurrentUser();
      setCurrentUser(user);

      const convos = await apiClient.getConversations();
      setConversations(convos);
    } catch (err: any) {
      setError(err.message || 'Failed to load data');
      if (err.message?.includes('401') || err.message?.includes('Unauthorized')) {
        navigate('/login');
      }
    } finally {
      setLoading(false);
    }
  };

  const loadMessages = async (userId: number) => {
    try {
      const msgs = await apiClient.getConversation(userId);
      setMessages(msgs);
    } catch (err: any) {
      setError(err.message || 'Failed to load messages');
    }
  };

  const handleMenuOpen = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget);
  };

  const handleMenuClose = () => {
    setAnchorEl(null);
  };

  const handleLogout = () => {
    apiClient.setToken(null);
    navigate('/');
  };

  const handleSendMessage = async () => {
    if (!message.trim() || !selectedUserId) return;

    const content = message.trim();
    setMessage('');

    try {
      if (isConnected) {
        sendMessage(selectedUserId, content);
        setMessages((prev) => [
          ...prev,
          {
            id: Date.now(),
            sender_id: currentUser.id,
            receiver_id: selectedUserId,
            content: content,
            content_filtered: content,
            message_type: 'text',
            is_flagged: false,
            created_at: new Date().toISOString(),
          },
        ]);
      } else {
        await apiClient.sendMessage(selectedUserId, content);
        await loadMessages(selectedUserId);
      }
    } catch (err: any) {
      setError(err.message || 'Failed to send message');
    }
  };

  const handleTyping = () => {
    if (!selectedUserId) return;
    sendTyping(selectedUserId, true);
    if (typingTimeoutRef.current) {
      clearTimeout(typingTimeoutRef.current);
    }
    typingTimeoutRef.current = setTimeout(() => {
      sendTyping(selectedUserId, false);
    }, 3000);
  };

  const handleImageUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file || !selectedUserId) return;

    if (file.size > 2 * 1024 * 1024) {
      setError('Image size too large. Please select an image under 2MB.');
      return;
    }

    const reader = new FileReader();
    reader.onloadend = () => {
      const base64String = reader.result as string;
      if (isConnected) {
        sendMessage(selectedUserId, base64String, 'image');
        setMessages((prev) => [
          ...prev,
          {
            id: Date.now(),
            sender_id: currentUser.id,
            receiver_id: selectedUserId,
            content: base64String,
            content_filtered: base64String,
            message_type: 'image',
            is_flagged: false,
            created_at: new Date().toISOString(),
          },
        ]);
      }
    };
    reader.readAsDataURL(file);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const handleReportAndBlock = async () => {
    if (!flaggedMessage || !selectedPeer) return;

    try {
      // Report the incident
      await apiClient.reportIncident(
        flaggedMessage.sender_id,
        'cyberbullying',
        `AI detected harmful content: ${flaggedMessage.content_filtered}`,
        flaggedMessage.id
      );

      // Block the user
      await apiClient.blockUserDirectly(flaggedMessage.sender_id);

      // Close dialog and clear selection
      setAlertDialogOpen(false);
      setFlaggedMessage(null);
      setSelectedUserId(null);
      setSelectedPeer(null);

      // Refresh conversations
      loadUserAndConversations();
    } catch (error) {
      console.error('Failed to report and block:', error);
    }
  };

  const handleReportOnly = async () => {
    if (!flaggedMessage) return;

    try {
      // Report the incident
      await apiClient.reportIncident(
        flaggedMessage.sender_id,
        'cyberbullying',
        `AI detected harmful content: ${flaggedMessage.content_filtered}`,
        flaggedMessage.id
      );

      // Close dialog
      setAlertDialogOpen(false);
      setFlaggedMessage(null);
    } catch (error) {
      console.error('Failed to report:', error);
    }
  };

  const handleDismissAlert = () => {
    setAlertDialogOpen(false);
    setFlaggedMessage(null);
  };

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }}>
        <CircularProgress />
      </Box>
    );
  }

  // Mobile View: Chat List vs Chat View
  const showChatList = !isMobile || !selectedUserId;
  const showChatView = !isMobile || !!selectedUserId;

  return (
    <Box sx={{ height: 'calc(100vh - 64px)', overflow: 'hidden', p: { xs: 0, md: 2 } }}>
      <Container maxWidth="xl" sx={{ height: '100%', p: { xs: 0, md: 2 } }}>
        <Box
          sx={{
            display: 'flex',
            height: '100%',
            gap: 3,
            position: 'relative',
          }}
        >
          {/* Chat List Sidebar */}
          <Paper
            className="glass-panel"
            sx={{
              width: { xs: '100%', md: 360 },
              display: showChatList ? 'flex' : 'none',
              flexDirection: 'column',
              borderRadius: { xs: 0, md: 4 },
              border: { xs: 'none', md: '1px solid rgba(255,255,255,0.5)' },
              overflow: 'hidden',
            }}
          >
            <Box sx={{ p: 2, borderBottom: '1px solid', borderColor: 'divider' }}>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                <Typography variant="h6" fontWeight={700}>
                  Messages
                </Typography>
                <IconButton size="small" onClick={() => navigate('/friends')}>
                  <PeopleRoundedIcon />
                </IconButton>
              </Box>
              <TextField
                fullWidth
                size="small"
                placeholder="Search..."
                value={conversationSearch}
                onChange={(e) => setConversationSearch(e.target.value)}
                InputProps={{
                  startAdornment: (
                    <InputAdornment position="start">
                      <SearchRoundedIcon fontSize="small" color="action" />
                    </InputAdornment>
                  ),
                  sx: { borderRadius: 3, bgcolor: 'background.default' }
                }}
              />
            </Box>

            {/* Search Results */}
            {conversationSearch.trim().length >= 2 && (
              <Box sx={{ px: 2, py: 1, borderBottom: '1px solid', borderColor: 'divider', bgcolor: 'background.default' }}>
                <Typography variant="caption" color="text.secondary" fontWeight={600}>
                  Search Results
                </Typography>
                {searchLoading ? (
                  <Box sx={{ display: 'flex', justifyContent: 'center', py: 2 }}>
                    <CircularProgress size={20} />
                  </Box>
                ) : (
                  <List dense>
                    {searchResults.map((user) => (
                      <ListItemButton key={user.id} onClick={() => handleSelectUser(user)} sx={{ borderRadius: 2 }}>
                        <ListItemAvatar>
                          <Avatar src={user.avatar_url} sx={{ width: 32, height: 32 }}>
                            {user.username[0].toUpperCase()}
                          </Avatar>
                        </ListItemAvatar>
                        <ListItemText primary={user.username} />
                      </ListItemButton>
                    ))}
                  </List>
                )}
              </Box>
            )}

            {/* Conversation List */}
            <List sx={{ flex: 1, overflowY: 'auto', px: 1 }}>
              {filteredConversations.map((conversation) => (
                <ListItemButton
                  key={conversation.user.id}
                  selected={selectedUserId === conversation.user.id}
                  onClick={() => handleSelectConversation(conversation)}
                  sx={{
                    borderRadius: 3,
                    mb: 0.5,
                    '&.Mui-selected': {
                      bgcolor: 'primary.light',
                      color: 'primary.main',
                      '&:hover': { bgcolor: 'primary.light' },
                    },
                  }}
                >
                  <ListItemAvatar>
                    <Badge
                      color={isConnected ? 'success' : 'default'}
                      variant="dot"
                      overlap="circular"
                      anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
                    >
                      <Avatar src={conversation.user.avatar_url}>
                        {conversation.user.username[0].toUpperCase()}
                      </Avatar>
                    </Badge>
                  </ListItemAvatar>
                  <ListItemText
                    primary={
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                        <Typography fontWeight={600} noWrap>
                          {conversation.user.username}
                        </Typography>
                        {conversation.user.has_red_tag && (
                          <Tooltip title="Red Tagged User">
                            <Box sx={{ fontSize: '0.9rem' }}>⚠️</Box>
                          </Tooltip>
                        )}
                      </Box>
                    }
                    secondary={
                      <Typography variant="body2" color="text.secondary" noWrap>
                        {conversation.last_message.content}
                      </Typography>
                    }
                  />
                  <Typography variant="caption" color="text.secondary" sx={{ ml: 1 }}>
                    {format(new Date(conversation.last_message.created_at), 'h:mm a')}
                  </Typography>
                </ListItemButton>
              ))}
            </List>
          </Paper>

          {/* Chat View */}
          <Paper
            className="glass-panel"
            sx={{
              flex: 1,
              display: showChatView ? 'flex' : 'none',
              flexDirection: 'column',
              borderRadius: { xs: 0, md: 4 },
              border: { xs: 'none', md: '1px solid rgba(255,255,255,0.5)' },
              overflow: 'hidden',
            }}
          >
            {activePeer ? (
              <>
                {/* Chat Header */}
                <Box
                  sx={{
                    p: 2,
                    borderBottom: '1px solid',
                    borderColor: 'divider',
                    display: 'flex',
                    alignItems: 'center',
                    gap: 2,
                    bgcolor: 'rgba(255,255,255,0.5)',
                    backdropFilter: 'blur(10px)',
                  }}
                >
                  {isMobile && (
                    <IconButton onClick={() => setSelectedUserId(null)}>
                      <ArrowBackRoundedIcon />
                    </IconButton>
                  )}
                  <Avatar src={activePeer.avatar_url}>
                    {activePeer.username[0].toUpperCase()}
                  </Avatar>
                  <Box sx={{ flex: 1 }}>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <Typography variant="subtitle1" fontWeight={700}>
                        {activePeer.username}
                      </Typography>
                      {activePeer.has_red_tag && (
                        <Tooltip title="Red Tagged User - Multiple Policy Violations">
                          <Box
                            sx={{
                              px: 1,
                              py: 0.25,
                              borderRadius: 1,
                              bgcolor: 'error.main',
                              color: 'white',
                              fontSize: '0.7rem',
                              fontWeight: 700,
                              display: 'flex',
                              alignItems: 'center',
                              gap: 0.5,
                            }}
                          >
                            ⚠️ RED TAG
                          </Box>
                        </Tooltip>
                      )}
                    </Box>
                    <Typography variant="caption" color="success.main" sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                      <Box sx={{ width: 6, height: 6, borderRadius: '50%', bgcolor: 'success.main' }} />
                      Active now
                    </Typography>
                  </Box>
                  <Stack direction="row">
                    <IconButton>
                      <PhoneRoundedIcon />
                    </IconButton>
                    <IconButton>
                      <VideocamRoundedIcon />
                    </IconButton>
                    <IconButton onClick={handleMenuOpen}>
                      <MoreVertRoundedIcon />
                    </IconButton>
                  </Stack>
                </Box>

                {/* Messages Area */}
                <Box sx={{ flex: 1, overflowY: 'auto', p: 3, bgcolor: 'rgba(249,250,251, 0.5)' }}>
                  {messages.map((msg) => {
                    const isOwn = msg.sender_id === currentUser?.id;
                    const isCyberBOT = msg.sender_id === 0 || msg.message_type === 'system_warning';
                    return (
                      <Box
                        key={msg.id}
                        sx={{
                          display: 'flex',
                          justifyContent: isCyberBOT ? 'center' : isOwn ? 'flex-end' : 'flex-start',
                          mb: 2,
                        }}
                      >
                        <Box
                          sx={{
                            maxWidth: isCyberBOT ? '85%' : '70%',
                            p: 2,
                            borderRadius: 3,
                            borderTopRightRadius: isOwn ? 4 : 3,
                            borderTopLeftRadius: isOwn ? 3 : 4,
                            bgcolor: isCyberBOT ? 'warning.light' : isOwn ? 'primary.main' : 'white',
                            color: isCyberBOT ? 'warning.dark' : isOwn ? 'white' : 'text.primary',
                            boxShadow: isCyberBOT ? '0 4px 12px rgba(237, 108, 2, 0.2)' : isOwn ? 'var(--shadow-md)' : '0 2px 4px rgba(0,0,0,0.05)',
                            background: isCyberBOT ? 'linear-gradient(135deg, #fff3e0 0%, #ffe0b2 100%)' : isOwn ? 'var(--gradient-primary)' : 'white',
                            border: isCyberBOT ? '2px solid' : 'none',
                            borderColor: isCyberBOT ? 'warning.main' : 'transparent',
                          }}
                        >
                          {isCyberBOT && (
                            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1, pb: 1, borderBottom: '1px solid', borderColor: 'warning.main' }}>
                              <Box sx={{ fontSize: '1.2rem' }}>🤖</Box>
                              <Typography variant="caption" fontWeight={700} color="warning.dark">
                                CyberBOT - Safety Alert
                              </Typography>
                            </Box>
                          )}
                          {msg.message_type === 'image' ? (
                            <Box sx={{ borderRadius: 2, overflow: 'hidden' }}>
                              <img
                                src={msg.content_filtered || msg.content}
                                alt="Shared"
                                style={{
                                  maxWidth: '100%',
                                  maxHeight: 300,
                                  display: 'block',
                                  filter: msg.is_flagged ? 'blur(10px)' : 'none'
                                }}
                              />
                            </Box>
                          ) : (
                            <Typography variant="body1" sx={{ wordBreak: 'break-word' }}>
                              {msg.content_filtered || msg.content}
                            </Typography>
                          )}
                          <Typography
                            variant="caption"
                            sx={{
                              display: 'block',
                              mt: 0.5,
                              textAlign: 'right',
                              opacity: 0.8,
                              fontSize: '0.7rem',
                            }}
                          >
                            {format(new Date(msg.created_at), 'h:mm a')}
                          </Typography>
                        </Box>
                      </Box>
                    );
                  })}
                  <div ref={messagesEndRef} />
                </Box>

                {/* Input Area */}
                <Box sx={{ p: 2, bgcolor: 'background.paper', borderTop: '1px solid', borderColor: 'divider' }}>
                  <Stack direction="row" spacing={1} alignItems="center">
                    <IconButton size="small" onClick={() => fileInputRef.current?.click()}>
                      <ImageRoundedIcon color="action" />
                    </IconButton>
                    <input
                      type="file"
                      ref={fileInputRef}
                      style={{ display: 'none' }}
                      accept="image/*"
                      onChange={handleImageUpload}
                    />
                    <IconButton size="small">
                      <AttachFileRoundedIcon color="action" />
                    </IconButton>
                    <TextField
                      fullWidth
                      size="small"
                      placeholder="Type a message..."
                      value={message}
                      onChange={(e) => {
                        setMessage(e.target.value);
                        handleTyping();
                      }}
                      onKeyDown={(e) => {
                        if (e.key === 'Enter' && !e.shiftKey) {
                          e.preventDefault();
                          handleSendMessage();
                        }
                      }}
                      sx={{
                        '& .MuiOutlinedInput-root': {
                          borderRadius: 4,
                          bgcolor: 'background.default',
                        }
                      }}
                    />
                    <IconButton
                      color="primary"
                      onClick={handleSendMessage}
                      disabled={!message.trim()}
                      sx={{
                        bgcolor: 'primary.main',
                        color: 'white',
                        '&:hover': { bgcolor: 'primary.dark' },
                        '&.Mui-disabled': { bgcolor: 'action.disabledBackground' }
                      }}
                    >
                      <SendRoundedIcon />
                    </IconButton>
                  </Stack>
                </Box>
              </>
            ) : (
              <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', p: 4, textAlign: 'center' }}>
                <Box
                  sx={{
                    width: 120,
                    height: 120,
                    borderRadius: '50%',
                    bgcolor: 'primary.light',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    mb: 3,
                    opacity: 0.5,
                  }}
                >
                  <SendRoundedIcon sx={{ fontSize: 60, color: 'primary.main' }} />
                </Box>
                <Typography variant="h5" fontWeight={700} gutterBottom>
                  Your Messages
                </Typography>
                <Typography variant="body1" color="text.secondary" sx={{ maxWidth: 400 }}>
                  Select a conversation from the list or start a new one to begin chatting securely.
                </Typography>
              </Box>
            )}
          </Paper>
        </Box>
      </Container>

      {/* Menu */}
      <Menu anchorEl={anchorEl} open={Boolean(anchorEl)} onClose={handleMenuClose}>
        <MenuItem onClick={() => { navigate('/profile'); handleMenuClose(); }}>
          <PersonRoundedIcon sx={{ mr: 1.5 }} /> Profile
        </MenuItem>
        <MenuItem onClick={() => { navigate('/friends'); handleMenuClose(); }}>
          <PeopleRoundedIcon sx={{ mr: 1.5 }} /> Friends
        </MenuItem>
        <MenuItem onClick={() => { navigate('/mental-health'); handleMenuClose(); }}>
          <PsychologyRoundedIcon sx={{ mr: 1.5 }} /> Mental Health
        </MenuItem>
        {isAdmin && (
          <MenuItem onClick={() => { navigate('/admin'); handleMenuClose(); }}>
            <AdminPanelSettingsRoundedIcon sx={{ mr: 1.5 }} /> Admin
          </MenuItem>
        )}
        <MenuItem onClick={handleLogout}>
          <LogoutRoundedIcon sx={{ mr: 1.5 }} /> Logout
        </MenuItem>
      </Menu>

      {/* AI Assistant FAB */}
      <Tooltip title="Talk to Aurora (AI Counselor)">
        <Fab
          color="secondary"
          onClick={() => navigate('/mental-health')}
          sx={{
            position: 'fixed',
            bottom: { xs: 80, md: 32 },
            right: 32,
            boxShadow: 'var(--shadow-xl)',
            background: 'var(--gradient-primary)',
          }}
        >
          <PsychologyRoundedIcon />
        </Fab>
      </Tooltip>

      {/* Cyberbullying Alert Dialog */}
      <CyberbullyingAlertDialog
        open={alertDialogOpen}
        onClose={handleDismissAlert}
        onReportAndBlock={handleReportAndBlock}
        onReportOnly={handleReportOnly}
        messageContent={flaggedMessage?.content_filtered || ''}
        severity={flaggedMessage?.severity_score as any || 'medium'}
        senderName={selectedPeer?.username || 'Unknown User'}
        categories={['cyberbullying']}
      />
    </Box>
  );
};

export default Chat;
