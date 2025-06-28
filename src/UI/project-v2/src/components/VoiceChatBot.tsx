import React, { useState, useRef, useEffect } from 'react';
import { Mic, MicOff, Send, Volume2, Loader2, MessageCircle, Zap, AlertCircle, Type, Moon, Sun } from 'lucide-react';
import { useAudioRecorder } from '../hooks/useAudioRecorder';
import { useTheme } from '../hooks/useTheme';

interface ChatMessage {
  id: string;
  type: 'user' | 'bot';
  text: string;
  timestamp: Date;
  audioUrl?: string;
  isVoice?: boolean;
}

interface ChatState {
  status: 'idle' | 'recording' | 'processing' | 'playing' | 'error';
  error?: string;
}

type ChatMode = 'voice' | 'text';
type ActiveTab = 'chat' | 'about' | 'features' | 'contact';

const VoiceChatBot: React.FC = () => {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [chatState, setChatState] = useState<ChatState>({ status: 'idle' });
  const [isPlaying, setIsPlaying] = useState(false);
  const [chatMode, setChatMode] = useState<ChatMode>('voice');
  const [textInput, setTextInput] = useState('');
  const [activeTab, setActiveTab] = useState<ActiveTab>('chat');
  
  const { theme, toggleTheme } = useTheme();
  const audioPlayerRef = useRef<HTMLAudioElement>(null);
  const {
    isRecording,
    audioBlob,
    startRecording,
    stopRecording,
    error: recordingError,
    duration
  } = useAudioRecorder();

  // Handle recording completion
  useEffect(() => {
    if (audioBlob && !isRecording) {
      handleSendVoiceMessage(audioBlob);
    }
  }, [audioBlob, isRecording]);

  const handleSendVoiceMessage = async (blob: Blob) => {
    setChatState({ status: 'processing' });
    
    try {
      const formData = new FormData();
      formData.append('file', blob, 'recording.webm');
      formData.append('model', 'gemini-2.5-flash-lite-preview-06-17');

      const response = await fetch('http://localhost:8000/chat-voice', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error(`Server error: ${response.status}`);
      }

      // Get transcription and answer from headers
      const transcription = response.headers.get('X-Transcription') || 'Audio transcribed';
      const answer = response.headers.get('X-Answer') || 'Response generated';

      // Add user message
      const userMessage: ChatMessage = {
        id: Date.now().toString() + '_user',
        type: 'user',
        text: transcription,
        timestamp: new Date(),
        isVoice: true,
      };

      // Get audio response
      const audioResponse = await response.blob();
      const audioUrl = URL.createObjectURL(audioResponse);

      // Add bot message
      const botMessage: ChatMessage = {
        id: Date.now().toString() + '_bot',
        type: 'bot',
        text: answer,
        timestamp: new Date(),
        audioUrl,
        isVoice: true,
      };

      setMessages(prev => [...prev, userMessage, botMessage]);
      
      // Auto-play response
      setChatState({ status: 'playing' });
      if (audioPlayerRef.current) {
        audioPlayerRef.current.src = audioUrl;
        audioPlayerRef.current.play();
      }

    } catch (error) {
      console.error('Voice chat error:', error);
      setChatState({ 
        status: 'error', 
        error: error instanceof Error ? error.message : 'Unknown error occurred' 
      });
    }
  };

  const handleSendTextMessage = async () => {
    if (!textInput.trim()) return;

    setChatState({ status: 'processing' });
    
    const userMessage: ChatMessage = {
      id: Date.now().toString() + '_user',
      type: 'user',
      text: textInput,
      timestamp: new Date(),
      isVoice: false,
    };

    setMessages(prev => [...prev, userMessage]);
    setTextInput('');

    try {
      const response = await fetch('http://localhost:8000/chat-text', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ question: textInput }),
      });

      if (!response.ok) {
        throw new Error(`Server error: ${response.status}`);
      }

      const result = await response.json();
      
      const botMessage: ChatMessage = {
        id: Date.now().toString() + '_bot',
        type: 'bot',
        text: result.answer,
        timestamp: new Date(),
        isVoice: false,
      };

      setMessages(prev => [...prev, botMessage]);
      setChatState({ status: 'idle' });

    } catch (error) {
      console.error('Text chat error:', error);
      setChatState({ 
        status: 'error', 
        error: error instanceof Error ? error.message : 'Unknown error occurred' 
      });
    }
  };

  const handleStartRecording = async () => {
    setChatState({ status: 'recording' });
    await startRecording();
  };

  const handleStopRecording = () => {
    stopRecording();
  };

  const handleAudioEnd = () => {
    setIsPlaying(false);
    setChatState({ status: 'idle' });
  };

  const handlePlayMessage = (audioUrl: string) => {
    if (audioPlayerRef.current) {
      audioPlayerRef.current.src = audioUrl;
      audioPlayerRef.current.play();
      setIsPlaying(true);
    }
  };

  const formatDuration = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const getStatusText = () => {
    switch (chatState.status) {
      case 'recording':
        return `Recording... ${formatDuration(duration)}`;
      case 'processing':
        return 'Processing your message...';
      case 'playing':
        return 'Playing response...';
      case 'error':
        return chatState.error || 'An error occurred';
      default:
        return 'Ready to chat';
    }
  };

  const getStatusColor = () => {
    const colors = {
      recording: theme === 'dark' ? 'text-red-400' : 'text-red-600',
      processing: theme === 'dark' ? 'text-blue-400' : 'text-blue-600',
      playing: theme === 'dark' ? 'text-green-400' : 'text-green-600',
      error: theme === 'dark' ? 'text-red-400' : 'text-red-600',
      default: theme === 'dark' ? 'text-gray-400' : 'text-gray-600',
    };
    
    return colors[chatState.status as keyof typeof colors] || colors.default;
  };

  const renderTabContent = () => {
    switch (activeTab) {
      case 'about':
        return (
          <div className={`max-w-4xl mx-auto px-6 py-8 ${theme === 'dark' ? 'text-gray-100' : 'text-gray-900'}`}>
            <div className="text-center mb-8">
              <h2 className="text-3xl font-bold mb-4">About Our AI Assistant</h2>
              <p className={`text-lg ${theme === 'dark' ? 'text-gray-300' : 'text-gray-600'} max-w-2xl mx-auto`}>
                We're revolutionizing communication with advanced AI technology that understands and responds in Vietnamese.
              </p>
            </div>
            
            <div className="grid md:grid-cols-2 gap-8 mb-12">
              <div className={`p-6 rounded-xl ${theme === 'dark' ? 'bg-gray-800' : 'bg-white'} shadow-lg`}>
                <h3 className="text-xl font-semibold mb-3">Our Mission</h3>
                <p className={theme === 'dark' ? 'text-gray-300' : 'text-gray-600'}>
                  To make AI accessible to Vietnamese speakers through natural voice interactions, 
                  breaking down language barriers and creating seamless human-AI communication.
                </p>
              </div>
              
              <div className={`p-6 rounded-xl ${theme === 'dark' ? 'bg-gray-800' : 'bg-white'} shadow-lg`}>
                <h3 className="text-xl font-semibold mb-3">Our Technology</h3>
                <p className={theme === 'dark' ? 'text-gray-300' : 'text-gray-600'}>
                  Powered by cutting-edge speech recognition, natural language processing, 
                  and text-to-speech synthesis specifically optimized for Vietnamese language.
                </p>
              </div>
            </div>
            
            <div className={`p-8 rounded-xl ${theme === 'dark' ? 'bg-gradient-to-r from-blue-900 to-purple-900' : 'bg-gradient-to-r from-blue-50 to-indigo-50'} text-center`}>
              <h3 className="text-2xl font-bold mb-4">Why Choose Us?</h3>
              <div className="grid md:grid-cols-3 gap-6">
                <div>
                  <div className={`w-12 h-12 ${theme === 'dark' ? 'bg-blue-600' : 'bg-blue-100'} rounded-lg flex items-center justify-center mx-auto mb-3`}>
                    <Zap className={`w-6 h-6 ${theme === 'dark' ? 'text-white' : 'text-blue-600'}`} />
                  </div>
                  <h4 className="font-semibold mb-2">Lightning Fast</h4>
                  <p className={`text-sm ${theme === 'dark' ? 'text-gray-300' : 'text-gray-600'}`}>
                    Real-time processing with minimal latency
                  </p>
                </div>
                <div>
                  <div className={`w-12 h-12 ${theme === 'dark' ? 'bg-green-600' : 'bg-green-100'} rounded-lg flex items-center justify-center mx-auto mb-3`}>
                    <MessageCircle className={`w-6 h-6 ${theme === 'dark' ? 'text-white' : 'text-green-600'}`} />
                  </div>
                  <h4 className="font-semibold mb-2">Natural Conversations</h4>
                  <p className={`text-sm ${theme === 'dark' ? 'text-gray-300' : 'text-gray-600'}`}>
                    Context-aware responses that feel human
                  </p>
                </div>
                <div>
                  <div className={`w-12 h-12 ${theme === 'dark' ? 'bg-purple-600' : 'bg-purple-100'} rounded-lg flex items-center justify-center mx-auto mb-3`}>
                    <Volume2 className={`w-6 h-6 ${theme === 'dark' ? 'text-white' : 'text-purple-600'}`} />
                  </div>
                  <h4 className="font-semibold mb-2">Perfect Pronunciation</h4>
                  <p className={`text-sm ${theme === 'dark' ? 'text-gray-300' : 'text-gray-600'}`}>
                    Natural Vietnamese voice synthesis
                  </p>
                </div>
              </div>
            </div>
          </div>
        );
        
      case 'features':
        return (
          <div className={`max-w-4xl mx-auto px-6 py-8 ${theme === 'dark' ? 'text-gray-100' : 'text-gray-900'}`}>
            <div className="text-center mb-8">
              <h2 className="text-3xl font-bold mb-4">Powerful Features</h2>
              <p className={`text-lg ${theme === 'dark' ? 'text-gray-300' : 'text-gray-600'} max-w-2xl mx-auto`}>
                Discover what makes our AI assistant the perfect companion for your daily conversations.
              </p>
            </div>
            
            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
              {[
                {
                  icon: Mic,
                  title: 'Voice Recognition',
                  description: 'Advanced speech-to-text with Vietnamese language optimization',
                  color: 'blue'
                },
                {
                  icon: Type,
                  title: 'Text Chat',
                  description: 'Traditional text-based conversations when voice isn\'t convenient',
                  color: 'green'
                },
                {
                  icon: Volume2,
                  title: 'Natural Speech',
                  description: 'High-quality text-to-speech with natural Vietnamese pronunciation',
                  color: 'purple'
                },
                {
                  icon: MessageCircle,
                  title: 'Context Awareness',
                  description: 'Remembers conversation history for more meaningful interactions',
                  color: 'orange'
                },
                {
                  icon: Zap,
                  title: 'Real-time Processing',
                  description: 'Lightning-fast responses with minimal waiting time',
                  color: 'red'
                },
                {
                  icon: Moon,
                  title: 'Dark Mode',
                  description: 'Comfortable viewing experience in any lighting condition',
                  color: 'indigo'
                }
              ].map((feature, index) => (
                <div key={index} className={`p-6 rounded-xl ${theme === 'dark' ? 'bg-gray-800' : 'bg-white'} shadow-lg hover:shadow-xl transition-shadow`}>
                  <div className={`w-12 h-12 bg-${feature.color}-${theme === 'dark' ? '600' : '100'} rounded-lg flex items-center justify-center mb-4`}>
                    <feature.icon className={`w-6 h-6 text-${feature.color}-${theme === 'dark' ? '400' : '600'}`} />
                  </div>
                  <h3 className="text-lg font-semibold mb-2">{feature.title}</h3>
                  <p className={`text-sm ${theme === 'dark' ? 'text-gray-300' : 'text-gray-600'}`}>
                    {feature.description}
                  </p>
                </div>
              ))}
            </div>
          </div>
        );
        
      case 'contact':
        return (
          <div className={`max-w-4xl mx-auto px-6 py-8 ${theme === 'dark' ? 'text-gray-100' : 'text-gray-900'}`}>
            <div className="text-center mb-8">
              <h2 className="text-3xl font-bold mb-4">Get In Touch</h2>
              <p className={`text-lg ${theme === 'dark' ? 'text-gray-300' : 'text-gray-600'} max-w-2xl mx-auto`}>
                Have questions or feedback? We'd love to hear from you.
              </p>
            </div>
            
            <div className="grid md:grid-cols-2 gap-8">
              <div className={`p-8 rounded-xl ${theme === 'dark' ? 'bg-gray-800' : 'bg-white'} shadow-lg`}>
                <h3 className="text-xl font-semibold mb-6">Contact Information</h3>
                <div className="space-y-4">
                  <div className="flex items-center space-x-3">
                    <div className={`w-10 h-10 ${theme === 'dark' ? 'bg-blue-600' : 'bg-blue-100'} rounded-lg flex items-center justify-center`}>
                      <MessageCircle className={`w-5 h-5 ${theme === 'dark' ? 'text-white' : 'text-blue-600'}`} />
                    </div>
                    <div>
                      <p className="font-medium">Email</p>
                      <p className={theme === 'dark' ? 'text-gray-300' : 'text-gray-600'}>support@voiceai.com</p>
                    </div>
                  </div>
                  
                  <div className="flex items-center space-x-3">
                    <div className={`w-10 h-10 ${theme === 'dark' ? 'bg-green-600' : 'bg-green-100'} rounded-lg flex items-center justify-center`}>
                      <Volume2 className={`w-5 h-5 ${theme === 'dark' ? 'text-white' : 'text-green-600'}`} />
                    </div>
                    <div>
                      <p className="font-medium">Phone</p>
                      <p className={theme === 'dark' ? 'text-gray-300' : 'text-gray-600'}>+84 123 456 789</p>
                    </div>
                  </div>
                  
                  <div className="flex items-center space-x-3">
                    <div className={`w-10 h-10 ${theme === 'dark' ? 'bg-purple-600' : 'bg-purple-100'} rounded-lg flex items-center justify-center`}>
                      <Zap className={`w-5 h-5 ${theme === 'dark' ? 'text-white' : 'text-purple-600'}`} />
                    </div>
                    <div>
                      <p className="font-medium">Address</p>
                      <p className={theme === 'dark' ? 'text-gray-300' : 'text-gray-600'}>Ho Chi Minh City, Vietnam</p>
                    </div>
                  </div>
                </div>
              </div>
              
              <div className={`p-8 rounded-xl ${theme === 'dark' ? 'bg-gray-800' : 'bg-white'} shadow-lg`}>
                <h3 className="text-xl font-semibold mb-6">Send us a Message</h3>
                <form className="space-y-4">
                  <div>
                    <label className={`block text-sm font-medium mb-2 ${theme === 'dark' ? 'text-gray-300' : 'text-gray-700'}`}>
                      Name
                    </label>
                    <input
                      type="text"
                      className={`w-full px-4 py-2 rounded-lg border ${
                        theme === 'dark' 
                          ? 'bg-gray-700 border-gray-600 text-white placeholder-gray-400' 
                          : 'bg-white border-gray-300 text-gray-900 placeholder-gray-500'
                      } focus:ring-2 focus:ring-blue-500 focus:border-transparent`}
                      placeholder="Your name"
                    />
                  </div>
                  
                  <div>
                    <label className={`block text-sm font-medium mb-2 ${theme === 'dark' ? 'text-gray-300' : 'text-gray-700'}`}>
                      Email
                    </label>
                    <input
                      type="email"
                      className={`w-full px-4 py-2 rounded-lg border ${
                        theme === 'dark' 
                          ? 'bg-gray-700 border-gray-600 text-white placeholder-gray-400' 
                          : 'bg-white border-gray-300 text-gray-900 placeholder-gray-500'
                      } focus:ring-2 focus:ring-blue-500 focus:border-transparent`}
                      placeholder="your@email.com"
                    />
                  </div>
                  
                  <div>
                    <label className={`block text-sm font-medium mb-2 ${theme === 'dark' ? 'text-gray-300' : 'text-gray-700'}`}>
                      Message
                    </label>
                    <textarea
                      rows={4}
                      className={`w-full px-4 py-2 rounded-lg border ${
                        theme === 'dark' 
                          ? 'bg-gray-700 border-gray-600 text-white placeholder-gray-400' 
                          : 'bg-white border-gray-300 text-gray-900 placeholder-gray-500'
                      } focus:ring-2 focus:ring-blue-500 focus:border-transparent`}
                      placeholder="Your message..."
                    />
                  </div>
                  
                  <button
                    type="submit"
                    className="w-full bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 px-4 rounded-lg transition-colors"
                  >
                    Send Message
                  </button>
                </form>
              </div>
            </div>
          </div>
        );
        
      default:
        return (
          <div className="flex-1 flex flex-col">
            {/* Chat Messages */}
            <div className="flex-1 max-w-4xl mx-auto w-full px-6 py-8 overflow-y-auto">
              {messages.length === 0 ? (
                <div className="text-center py-12">
                  <div className={`p-4 ${theme === 'dark' ? 'bg-blue-900' : 'bg-blue-100'} rounded-full w-16 h-16 mx-auto mb-4 flex items-center justify-center`}>
                    {chatMode === 'voice' ? (
                      <Mic className={`w-8 h-8 ${theme === 'dark' ? 'text-blue-400' : 'text-blue-600'}`} />
                    ) : (
                      <Type className={`w-8 h-8 ${theme === 'dark' ? 'text-blue-400' : 'text-blue-600'}`} />
                    )}
                  </div>
                  <h3 className={`text-lg font-medium mb-2 ${theme === 'dark' ? 'text-gray-100' : 'text-gray-900'}`}>
                    Start a conversation
                  </h3>
                  <p className={`max-w-md mx-auto ${theme === 'dark' ? 'text-gray-400' : 'text-gray-600'}`}>
                    {chatMode === 'voice' 
                      ? 'Press and hold the microphone button to record your question. I\'ll listen, understand, and respond with both text and voice.'
                      : 'Type your question below and I\'ll provide you with a helpful response.'
                    }
                  </p>
                </div>
              ) : (
                <div className="space-y-6">
                  {messages.map((message) => (
                    <div
                      key={message.id}
                      className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}
                    >
                      <div
                        className={`max-w-xs lg:max-w-md px-4 py-3 rounded-2xl ${
                          message.type === 'user'
                            ? 'bg-blue-600 text-white'
                            : theme === 'dark'
                            ? 'bg-gray-800 text-gray-100 border border-gray-700'
                            : 'bg-white text-gray-900 shadow-md border border-gray-100'
                        }`}
                      >
                        <p className="text-sm leading-relaxed">{message.text}</p>
                        <div className="flex items-center justify-between mt-2">
                          <div className="flex items-center space-x-2">
                            <span
                              className={`text-xs ${
                                message.type === 'user' 
                                  ? 'text-blue-100' 
                                  : theme === 'dark' 
                                  ? 'text-gray-400' 
                                  : 'text-gray-500'
                              }`}
                            >
                              {message.timestamp.toLocaleTimeString()}
                            </span>
                            {message.isVoice && (
                              <span
                                className={`text-xs px-2 py-1 rounded-full ${
                                  message.type === 'user'
                                    ? 'bg-blue-700 text-blue-100'
                                    : theme === 'dark'
                                    ? 'bg-gray-700 text-gray-300'
                                    : 'bg-gray-100 text-gray-600'
                                }`}
                              >
                                Voice
                              </span>
                            )}
                          </div>
                          {message.audioUrl && (
                            <button
                              onClick={() => handlePlayMessage(message.audioUrl!)}
                              className={`ml-2 p-1 rounded-full transition-colors ${
                                message.type === 'user' 
                                  ? 'hover:bg-blue-700' 
                                  : theme === 'dark'
                                  ? 'hover:bg-gray-700'
                                  : 'hover:bg-gray-100'
                              }`}
                            >
                              <Volume2 className="w-3 h-3" />
                            </button>
                          )}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Status Bar */}
            <div className={`${theme === 'dark' ? 'bg-gray-800/90' : 'bg-white/90'} backdrop-blur-sm border-t ${theme === 'dark' ? 'border-gray-700' : 'border-gray-200'} px-6 py-3`}>
              <div className="max-w-4xl mx-auto flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  {chatState.status === 'processing' && (
                    <Loader2 className={`w-4 h-4 animate-spin ${theme === 'dark' ? 'text-blue-400' : 'text-blue-600'}`} />
                  )}
                  {chatState.status === 'error' && (
                    <AlertCircle className={`w-4 h-4 ${theme === 'dark' ? 'text-red-400' : 'text-red-600'}`} />
                  )}
                  {chatState.status === 'recording' && (
                    <div className="w-4 h-4 bg-red-600 rounded-full animate-pulse" />
                  )}
                  <span className={`text-sm font-medium ${getStatusColor()}`}>
                    {getStatusText()}
                  </span>
                </div>
                {recordingError && (
                  <span className={`text-sm ${theme === 'dark' ? 'text-red-400' : 'text-red-600'}`}>
                    {recordingError}
                  </span>
                )}
              </div>
            </div>

            {/* Input Area */}
            <div className={`${theme === 'dark' ? 'bg-gray-800' : 'bg-white'} border-t ${theme === 'dark' ? 'border-gray-700' : 'border-gray-200'} px-6 py-6`}>
              <div className="max-w-4xl mx-auto">
                {/* Chat Mode Toggle */}
                <div className="flex justify-center mb-6">
                  <div className={`p-1 rounded-lg ${theme === 'dark' ? 'bg-gray-700' : 'bg-gray-100'}`}>
                    <button
                      onClick={() => setChatMode('voice')}
                      className={`px-4 py-2 rounded-md text-sm font-medium transition-all ${
                        chatMode === 'voice'
                          ? 'bg-blue-600 text-white shadow-sm'
                          : theme === 'dark'
                          ? 'text-gray-300 hover:text-white'
                          : 'text-gray-600 hover:text-gray-900'
                      }`}
                    >
                      <Mic className="w-4 h-4 inline mr-2" />
                      Voice Chat
                    </button>
                    <button
                      onClick={() => setChatMode('text')}
                      className={`px-4 py-2 rounded-md text-sm font-medium transition-all ${
                        chatMode === 'text'
                          ? 'bg-blue-600 text-white shadow-sm'
                          : theme === 'dark'
                          ? 'text-gray-300 hover:text-white'
                          : 'text-gray-600 hover:text-gray-900'
                      }`}
                    >
                      <Type className="w-4 h-4 inline mr-2" />
                      Text Chat
                    </button>
                  </div>
                </div>

                {/* Input Controls */}
                {chatMode === 'voice' ? (
                  <div className="flex justify-center">
                    <button
                      onMouseDown={handleStartRecording}
                      onMouseUp={handleStopRecording}
                      onTouchStart={handleStartRecording}
                      onTouchEnd={handleStopRecording}
                      disabled={chatState.status === 'processing'}
                      className={`
                        relative p-6 rounded-full transition-all duration-200 transform hover:scale-105 active:scale-95
                        ${
                          isRecording
                            ? 'bg-red-600 hover:bg-red-700 shadow-lg shadow-red-200'
                            : chatState.status === 'processing'
                            ? 'bg-gray-400 cursor-not-allowed'
                            : 'bg-blue-600 hover:bg-blue-700 shadow-lg shadow-blue-200'
                        }
                        ${isRecording ? 'animate-pulse' : ''}
                      `}
                    >
                      {chatState.status === 'processing' ? (
                        <Loader2 className="w-8 h-8 text-white animate-spin" />
                      ) : isRecording ? (
                        <MicOff className="w-8 h-8 text-white" />
                      ) : (
                        <Mic className="w-8 h-8 text-white" />
                      )}
                      
                      {/* Recording animation */}
                      {isRecording && (
                        <div className="absolute inset-0 rounded-full border-4 border-red-300 animate-ping" />
                      )}
                    </button>
                  </div>
                ) : (
                  <div className="flex space-x-4">
                    <input
                      type="text"
                      value={textInput}
                      onChange={(e) => setTextInput(e.target.value)}
                      onKeyPress={(e) => e.key === 'Enter' && handleSendTextMessage()}
                      placeholder="Type your message..."
                      disabled={chatState.status === 'processing'}
                      className={`flex-1 px-4 py-3 rounded-lg border ${
                        theme === 'dark'
                          ? 'bg-gray-700 border-gray-600 text-white placeholder-gray-400'
                          : 'bg-white border-gray-300 text-gray-900 placeholder-gray-500'
                      } focus:ring-2 focus:ring-blue-500 focus:border-transparent`}
                    />
                    <button
                      onClick={handleSendTextMessage}
                      disabled={!textInput.trim() || chatState.status === 'processing'}
                      className="px-6 py-3 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white rounded-lg transition-colors"
                    >
                      {chatState.status === 'processing' ? (
                        <Loader2 className="w-5 h-5 animate-spin" />
                      ) : (
                        <Send className="w-5 h-5" />
                      )}
                    </button>
                  </div>
                )}

                <p className={`text-center text-sm mt-4 ${theme === 'dark' ? 'text-gray-400' : 'text-gray-600'}`}>
                  {chatMode === 'voice' 
                    ? (isRecording ? 'Release to send' : 'Press and hold to record')
                    : 'Press Enter or click send to submit your message'
                  }
                </p>
              </div>
            </div>
          </div>
        );
    }
  };

  return (
    <div className={`min-h-screen transition-colors ${
      theme === 'dark' 
        ? 'bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900' 
        : 'bg-gradient-to-br from-blue-50 via-white to-indigo-50'
    }`}>
      {/* Header */}
      <div className={`${theme === 'dark' ? 'bg-gray-800/80' : 'bg-white/80'} backdrop-blur-sm border-b ${theme === 'dark' ? 'border-gray-700' : 'border-gray-200'} px-6 py-4`}>
        <div className="max-w-6xl mx-auto flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className={`p-2 ${theme === 'dark' ? 'bg-blue-900' : 'bg-blue-100'} rounded-lg`}>
              <MessageCircle className={`w-6 h-6 ${theme === 'dark' ? 'text-blue-400' : 'text-blue-600'}`} />
            </div>
            <div>
              <h1 className={`text-xl font-semibold ${theme === 'dark' ? 'text-gray-100' : 'text-gray-900'}`}>
                Voice Assistant
              </h1>
              <p className={`text-sm ${theme === 'dark' ? 'text-gray-400' : 'text-gray-500'}`}>
                Speak naturally in Vietnamese
              </p>
            </div>
          </div>
          
          <div className="flex items-center space-x-4">
            <div className="flex items-center space-x-2">
              <Zap className={`w-4 h-4 ${theme === 'dark' ? 'text-green-400' : 'text-green-500'}`} />
              <span className={`text-sm font-medium ${theme === 'dark' ? 'text-gray-300' : 'text-gray-700'}`}>
                AI Powered
              </span>
            </div>
            
            <button
              onClick={toggleTheme}
              className={`p-2 rounded-lg transition-colors ${
                theme === 'dark' 
                  ? 'bg-gray-700 hover:bg-gray-600 text-gray-300' 
                  : 'bg-gray-100 hover:bg-gray-200 text-gray-600'
              }`}
            >
              {theme === 'dark' ? (
                <Sun className="w-5 h-5" />
              ) : (
                <Moon className="w-5 h-5" />
              )}
            </button>
          </div>
        </div>
      </div>

      {/* Navigation Tabs */}
      <div className={`${theme === 'dark' ? 'bg-gray-800/50' : 'bg-white/50'} backdrop-blur-sm border-b ${theme === 'dark' ? 'border-gray-700' : 'border-gray-200'}`}>
        <div className="max-w-6xl mx-auto px-6">
          <nav className="flex space-x-8">
            {[
              { id: 'chat', label: 'Chat', icon: MessageCircle },
              { id: 'about', label: 'About Us', icon: Zap },
              { id: 'features', label: 'Features', icon: Volume2 },
              { id: 'contact', label: 'Contact', icon: Send },
            ].map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as ActiveTab)}
                className={`flex items-center space-x-2 py-4 border-b-2 transition-colors ${
                  activeTab === tab.id
                    ? 'border-blue-600 text-blue-600'
                    : theme === 'dark'
                    ? 'border-transparent text-gray-400 hover:text-gray-200'
                    : 'border-transparent text-gray-500 hover:text-gray-700'
                }`}
              >
                <tab.icon className="w-4 h-4" />
                <span className="font-medium">{tab.label}</span>
              </button>
            ))}
          </nav>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex flex-col">
        {renderTabContent()}
      </div>

      {/* Hidden audio player */}
      <audio
        ref={audioPlayerRef}
        onEnded={handleAudioEnd}
        onPlay={() => setIsPlaying(true)}
        onPause={() => setIsPlaying(false)}
        style={{ display: 'none' }}
      />
    </div>
  );
};

export default VoiceChatBot;