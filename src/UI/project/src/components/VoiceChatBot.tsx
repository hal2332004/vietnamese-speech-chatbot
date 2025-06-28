import React, { useState, useRef, useEffect } from 'react';
import { Mic, MicOff, Send, Volume2, Loader2, MessageCircle, Zap, AlertCircle, Type, Moon, Sun, Coffee, Book, Sparkles, Heart } from 'lucide-react';
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
  const [recordedAudioUrl, setRecordedAudioUrl] = useState<string | null>(null);
  
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
      const url = URL.createObjectURL(audioBlob);
      setRecordedAudioUrl(url);
      handleSendVoiceMessage(audioBlob);
    }
  }, [audioBlob, isRecording]);

  const handleSendVoiceMessage = async (blob: Blob) => {
    setChatState({ status: 'processing' });
    
    try {
      const formData = new FormData();
      const audioFile = new File([blob], 'recording.wav', { type: 'audio/wav' });

      formData.append('file', audioFile);
      formData.append('model', 'gemini-2.0-flash');

      const response = await fetch('http://localhost:8000/chat-voice', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error(`Server error: ${response.status}`);
      }

      const transcription = response.headers.get('X-Transcription') || 'Audio transcribed';
      const answer = response.headers.get('X-Answer') || 'Response generated';

      const userMessage: ChatMessage = {
        id: Date.now().toString() + '_user',
        type: 'user',
        text: transcription,
        timestamp: new Date(),
        isVoice: true,
      };

      const audioResponse = await response.blob();
      const audioUrl = URL.createObjectURL(audioResponse);

      const botMessage: ChatMessage = {
        id: Date.now().toString() + '_bot',
        type: 'bot',
        text: answer,
        timestamp: new Date(),
        audioUrl,
        isVoice: true,
      };

      setMessages(prev => [...prev, userMessage, botMessage]);
      
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
      const response = await fetch('http://localhost:8000/chat-text-stream', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ question: textInput }),
      });

      if (!response.ok || !response.body) {
        throw new Error(`Server error: ${response.status}`);
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder('utf-8');
      let botText = '';
      let done = false;

      const botMessage: ChatMessage = {
        id: Date.now().toString() + '_bot',
        type: 'bot',
        text: '',
        timestamp: new Date(),
        isVoice: false,
      };
      setMessages(prev => [...prev, botMessage]);

      while (!done) {
        const { value, done: doneReading } = await reader.read();
        done = doneReading;
        if (value) {
          const chunk = decoder.decode(value);
          botText += chunk;
          setMessages(prev => {
            const updated = [...prev];
            const lastIdx = updated.findIndex(m => m.id === botMessage.id);
            if (lastIdx !== -1) {
              updated[lastIdx] = { ...updated[lastIdx], text: botText };
            }
            return updated;
          });
        }
      }

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
        return 'Thinking deeply...';
      case 'playing':
        return 'Speaking response...';
      case 'error':
        return chatState.error || 'Something went awry';
      default:
        return 'Ready to chat, dear friend ✨';
    }
  };

  const getStatusColor = () => {
    const colors = {
      recording: theme === 'dark' ? 'text-red-300' : 'text-red-700',
      processing: theme === 'dark' ? 'text-amber-300' : 'text-amber-700',
      playing: theme === 'dark' ? 'text-emerald-300' : 'text-emerald-700',
      error: theme === 'dark' ? 'text-red-300' : 'text-red-700',
      default: theme === 'dark' ? 'text-warm-gray-400' : 'text-warm-gray-600',
    };
    
    return colors[chatState.status as keyof typeof colors] || colors.default;
  };

  const renderTabContent = () => {
    switch (activeTab) {
      case 'about':
        return (
          <div className={`max-w-4xl mx-auto px-8 py-12 ${theme === 'dark' ? 'text-warm-gray-100' : 'text-warm-gray-900'}`}>
            <div className="text-center mb-12">
              <div className="inline-flex items-center justify-center w-20 h-20 bg-gradient-to-br from-amber-100 to-orange-100 rounded-full mb-6 shadow-lg">
                <Book className="w-10 h-10 text-amber-700" />
              </div>
              <h2 className="text-4xl font-serif font-bold mb-6 text-transparent bg-clip-text bg-gradient-to-r from-amber-700 to-orange-600">
                Our Story
              </h2>
              <p className={`text-xl leading-relaxed ${theme === 'dark' ? 'text-warm-gray-300' : 'text-warm-gray-700'} max-w-3xl mx-auto font-serif italic`}>
                "In the golden age of conversation, we bridge the past and future with the warmth of human connection and the wisdom of artificial intelligence."
              </p>
            </div>
            
            <div className="grid md:grid-cols-2 gap-10 mb-16">
              <div className={`p-8 rounded-2xl ${theme === 'dark' ? 'bg-warm-gray-800 bg-opacity-50' : 'bg-warm-gray-50'} shadow-xl border ${theme === 'dark' ? 'border-warm-gray-700' : 'border-warm-gray-200'} backdrop-blur-sm`}>
                <div className="flex items-center mb-4">
                  <div className="w-12 h-12 bg-gradient-to-br from-amber-200 to-orange-200 rounded-xl flex items-center justify-center mr-4">
                    <Heart className="w-6 h-6 text-amber-700" />
                  </div>
                  <h3 className="text-2xl font-serif font-semibold">Our Heritage</h3>
                </div>
                <p className={`${theme === 'dark' ? 'text-warm-gray-300' : 'text-warm-gray-700'} leading-relaxed font-serif`}>
                  Born from a love of thoughtful conversation and timeless design, our AI assistant embodies the elegance of classical communication with the power of modern technology.
                </p>
              </div>
              
              <div className={`p-8 rounded-2xl ${theme === 'dark' ? 'bg-warm-gray-800 bg-opacity-50' : 'bg-warm-gray-50'} shadow-xl border ${theme === 'dark' ? 'border-warm-gray-700' : 'border-warm-gray-200'} backdrop-blur-sm`}>
                <div className="flex items-center mb-4">
                  <div className="w-12 h-12 bg-gradient-to-br from-emerald-200 to-teal-200 rounded-xl flex items-center justify-center mr-4">
                    <Sparkles className="w-6 h-6 text-emerald-700" />
                  </div>
                  <h3 className="text-2xl font-serif font-semibold">Our Philosophy</h3>
                </div>
                <p className={`${theme === 'dark' ? 'text-warm-gray-300' : 'text-warm-gray-700'} leading-relaxed font-serif`}>
                  Technology should feel like a warm conversation with an old friend - natural, thoughtful, and enriching. We craft experiences that honor both innovation and tradition.
                </p>
              </div>
            </div>
            
            <div className={`p-12 rounded-3xl ${theme === 'dark' ? 'bg-gradient-to-br from-amber-900 to-orange-900' : 'bg-gradient-to-br from-amber-50 to-orange-50'} relative overflow-hidden`}>
              {/* Decorative elements */}
              <div className="absolute top-0 left-0 w-full h-full opacity-10">
                <div className="absolute top-6 left-6 w-32 h-32 border-2 border-amber-400 rounded-full animate-pulse"></div>
                <div className="absolute bottom-6 right-6 w-24 h-24 border-2 border-orange-400 rounded-full animate-pulse" style={{ animationDelay: '1s' }}></div>
                <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 w-40 h-40 border border-amber-300 rounded-full animate-pulse" style={{ animationDelay: '2s' }}></div>
              </div>
              
              <div className="relative z-10 text-center">
                <h3 className="text-3xl font-serif font-bold mb-8 text-transparent bg-clip-text bg-gradient-to-r from-amber-700 to-orange-600">
                  The Vintage Promise
                </h3>
                
                <div className="grid md:grid-cols-3 gap-8">
                  {[
                    {
                      icon: Coffee,
                      title: 'Thoughtful Responses',
                      description: 'Like a good conversation over coffee, we take time to understand and respond meaningfully.',
                      color: 'amber'
                    },
                    {
                      icon: Book,
                      title: 'Timeless Wisdom',
                      description: 'Drawing from vast knowledge while maintaining the charm of classic conversation.',
                      color: 'emerald'
                    },
                    {
                      icon: Heart,
                      title: 'Human Connection',
                      description: 'Technology that feels personal, warm, and genuinely helpful in your daily life.',
                      color: 'rose'
                    }
                  ].map((feature, index) => (
                    <div key={index} className="group">
                      <div className={`transform transition-all duration-500 hover:scale-105 ${theme === 'dark' ? 'bg-warm-gray-800 bg-opacity-60' : 'bg-white bg-opacity-80'} backdrop-blur-sm rounded-2xl p-6 shadow-lg hover:shadow-2xl border ${theme === 'dark' ? 'border-warm-gray-700' : 'border-warm-gray-200'}`}>
                        <div className={`w-16 h-16 bg-gradient-to-br from-${feature.color}-200 to-${feature.color}-300 rounded-2xl flex items-center justify-center mx-auto mb-4 group-hover:rotate-12 transition-transform duration-300`}>
                          <feature.icon className={`w-8 h-8 text-${feature.color}-700`} />
                        </div>
                        <h4 className="font-serif font-semibold text-lg mb-3">{feature.title}</h4>
                        <p className={`text-sm ${theme === 'dark' ? 'text-warm-gray-300' : 'text-warm-gray-700'} leading-relaxed font-serif`}>
                          {feature.description}
                        </p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        );
        
      case 'features':
        return (
          <div className={`max-w-4xl mx-auto px-8 py-12 ${theme === 'dark' ? 'text-warm-gray-100' : 'text-warm-gray-900'}`}>
            <div className="text-center mb-12">
              <div className="inline-flex items-center justify-center w-20 h-20 bg-gradient-to-br from-emerald-100 to-teal-100 rounded-full mb-6 shadow-lg">
                <Sparkles className="w-10 h-10 text-emerald-700" />
              </div>
              <h2 className="text-4xl font-serif font-bold mb-6 text-transparent bg-clip-text bg-gradient-to-r from-emerald-700 to-teal-600">
                Exquisite Features
              </h2>
              <p className={`text-xl leading-relaxed ${theme === 'dark' ? 'text-warm-gray-300' : 'text-warm-gray-700'} max-w-3xl mx-auto font-serif italic`}>
                "Every feature crafted with the attention to detail of a master artisan, designed for the discerning conversationalist."
              </p>
            </div>
            
            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
              {[
                {
                  icon: Mic,
                  title: 'Voice Recognition',
                  description: 'Sophisticated speech-to-text that understands the nuances of Vietnamese conversation',
                  color: 'from-blue-200 to-indigo-200',
                  textColor: 'text-blue-700'
                },
                {
                  icon: Type,
                  title: 'Elegant Typography',
                  description: 'Beautiful text conversations with Claude-inspired typography for maximum readability',
                  color: 'from-emerald-200 to-teal-200',
                  textColor: 'text-emerald-700'
                },
                {
                  icon: Volume2,
                  title: 'Natural Speech',
                  description: 'Warm, natural Vietnamese voice synthesis that feels like a friendly conversation',
                  color: 'from-purple-200 to-pink-200',
                  textColor: 'text-purple-700'
                },
                {
                  icon: MessageCircle,
                  title: 'Contextual Memory',
                  description: 'Remembers our conversation history to provide more thoughtful, relevant responses',
                  color: 'from-amber-200 to-orange-200',
                  textColor: 'text-amber-700'
                },
                {
                  icon: Zap,
                  title: 'Instant Responses',
                  description: 'Lightning-fast processing while maintaining the warmth of human conversation',
                  color: 'from-rose-200 to-red-200',
                  textColor: 'text-rose-700'
                },
                {
                  icon: Coffee,
                  title: 'Vintage Aesthetic',
                  description: 'A timeless design that feels both classic and contemporary, like a well-aged wine',
                  color: 'from-yellow-200 to-amber-200',
                  textColor: 'text-yellow-700'
                }
              ].map((feature, index) => (
                <div key={index} className={`group p-8 rounded-2xl ${theme === 'dark' ? 'bg-warm-gray-800 bg-opacity-50' : 'bg-warm-gray-50'} shadow-xl border ${theme === 'dark' ? 'border-warm-gray-700' : 'border-warm-gray-200'} hover:shadow-2xl transition-all duration-300 backdrop-blur-sm`}>
                  <div className={`w-16 h-16 bg-gradient-to-br ${feature.color} rounded-2xl flex items-center justify-center mb-6 group-hover:scale-110 transition-transform duration-300`}>
                    <feature.icon className={`w-8 h-8 ${feature.textColor}`} />
                  </div>
                  <h3 className="text-xl font-serif font-semibold mb-4">{feature.title}</h3>
                  <p className={`text-sm ${theme === 'dark' ? 'text-warm-gray-300' : 'text-warm-gray-700'} leading-relaxed font-serif`}>
                    {feature.description}
                  </p>
                </div>
              ))}
            </div>
          </div>
        );
        
      case 'contact':
        return (
          <div className={`max-w-4xl mx-auto px-8 py-12 ${theme === 'dark' ? 'text-warm-gray-100' : 'text-warm-gray-900'}`}>
            <div className="text-center mb-12">
              <div className="inline-flex items-center justify-center w-20 h-20 bg-gradient-to-br from-rose-100 to-pink-100 rounded-full mb-6 shadow-lg">
                <Send className="w-10 h-10 text-rose-700" />
              </div>
              <h2 className="text-4xl font-serif font-bold mb-6 text-transparent bg-clip-text bg-gradient-to-r from-rose-700 to-pink-600">
                Let's Connect
              </h2>
              <p className={`text-xl leading-relaxed ${theme === 'dark' ? 'text-warm-gray-300' : 'text-warm-gray-700'} max-w-3xl mx-auto font-serif italic`}>
                "We'd be delighted to hear from you. Your thoughts and feedback help us create better conversational experiences."
              </p>
            </div>
            
            <div className="grid md:grid-cols-2 gap-12">
              <div className={`p-10 rounded-2xl ${theme === 'dark' ? 'bg-warm-gray-800 bg-opacity-50' : 'bg-warm-gray-50'} shadow-xl border ${theme === 'dark' ? 'border-warm-gray-700' : 'border-warm-gray-200'} backdrop-blur-sm`}>
                <h3 className="text-2xl font-serif font-semibold mb-8">Get in Touch</h3>
                <div className="space-y-6">
                  {[
                    {
                      icon: MessageCircle,
                      title: 'Email',
                      detail: 'hello@vintageai.com',
                      color: 'from-blue-200 to-indigo-200',
                      textColor: 'text-blue-700'
                    },
                    {
                      icon: Volume2,
                      title: 'Phone',
                      detail: '+84 123 456 789',
                      color: 'from-emerald-200 to-teal-200',
                      textColor: 'text-emerald-700'
                    },
                    {
                      icon: Coffee,
                      title: 'Address',
                      detail: 'Ho Chi Minh City, Vietnam',
                      color: 'from-amber-200 to-orange-200',
                      textColor: 'text-amber-700'
                    }
                  ].map((contact, index) => (
                    <div key={index} className="flex items-center space-x-4">
                      <div className={`w-14 h-14 bg-gradient-to-br ${contact.color} rounded-xl flex items-center justify-center`}>
                        <contact.icon className={`w-6 h-6 ${contact.textColor}`} />
                      </div>
                      <div>
                        <p className="font-serif font-semibold text-lg">{contact.title}</p>
                        <p className={`${theme === 'dark' ? 'text-warm-gray-300' : 'text-warm-gray-700'} font-serif`}>{contact.detail}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
              
              <div className={`p-10 rounded-2xl ${theme === 'dark' ? 'bg-warm-gray-800 bg-opacity-50' : 'bg-warm-gray-50'} shadow-xl border ${theme === 'dark' ? 'border-warm-gray-700' : 'border-warm-gray-200'} backdrop-blur-sm`}>
                <h3 className="text-2xl font-serif font-semibold mb-8">Send a Message</h3>
                <form className="space-y-6">
                  <div>
                    <label className={`block text-sm font-serif font-medium mb-3 ${theme === 'dark' ? 'text-warm-gray-300' : 'text-warm-gray-700'}`}>
                      Your Name
                    </label>
                    <input
                      type="text"
                      className={`w-full px-4 py-3 rounded-xl border-2 ${
                        theme === 'dark' 
                          ? 'bg-warm-gray-700 border-warm-gray-600 text-white placeholder-warm-gray-400' 
                          : 'bg-white border-warm-gray-300 text-warm-gray-900 placeholder-warm-gray-500'
                      } focus:ring-2 focus:ring-amber-500 focus:border-transparent transition-all font-serif`}
                      placeholder="Enter your name"
                    />
                  </div>
                  
                  <div>
                    <label className={`block text-sm font-serif font-medium mb-3 ${theme === 'dark' ? 'text-warm-gray-300' : 'text-warm-gray-700'}`}>
                      Email Address
                    </label>
                    <input
                      type="email"
                      className={`w-full px-4 py-3 rounded-xl border-2 ${
                        theme === 'dark' 
                          ? 'bg-warm-gray-700 border-warm-gray-600 text-white placeholder-warm-gray-400' 
                          : 'bg-white border-warm-gray-300 text-warm-gray-900 placeholder-warm-gray-500'
                      } focus:ring-2 focus:ring-amber-500 focus:border-transparent transition-all font-serif`}
                      placeholder="your@email.com"
                    />
                  </div>
                  
                  <div>
                    <label className={`block text-sm font-serif font-medium mb-3 ${theme === 'dark' ? 'text-warm-gray-300' : 'text-warm-gray-700'}`}>
                      Your Message
                    </label>
                    <textarea
                      rows={4}
                      className={`w-full px-4 py-3 rounded-xl border-2 ${
                        theme === 'dark' 
                          ? 'bg-warm-gray-700 border-warm-gray-600 text-white placeholder-warm-gray-400' 
                          : 'bg-white border-warm-gray-300 text-warm-gray-900 placeholder-warm-gray-500'
                      } focus:ring-2 focus:ring-amber-500 focus:border-transparent transition-all font-serif`}
                      placeholder="Share your thoughts with us..."
                    />
                  </div>
                  
                  <button
                    type="submit"
                    className="w-full bg-gradient-to-r from-amber-600 to-orange-600 hover:from-amber-700 hover:to-orange-700 text-white font-serif font-semibold py-3 px-6 rounded-xl transition-all duration-300 shadow-lg hover:shadow-xl transform hover:scale-105"
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
            <div className="flex-1 max-w-4xl mx-auto w-full px-8 py-12 overflow-y-auto">
              {messages.length === 0 ? (
                <div className="text-center py-16">
                  <div className={`p-6 bg-gradient-to-br from-amber-100 to-orange-100 rounded-3xl w-24 h-24 mx-auto mb-8 flex items-center justify-center shadow-lg`}>
                    {chatMode === 'voice' ? (
                      <Mic className="w-12 h-12 text-amber-700" />
                    ) : (
                      <Type className="w-12 h-12 text-amber-700" />
                    )}
                  </div>
                  <h3 className={`text-2xl font-serif font-semibold mb-4 ${theme === 'dark' ? 'text-warm-gray-100' : 'text-warm-gray-900'}`}>
                    Welcome, dear friend!
                  </h3>
                  <p className={`max-w-md mx-auto font-serif leading-relaxed ${theme === 'dark' ? 'text-warm-gray-400' : 'text-warm-gray-600'}`}>
                    {chatMode === 'voice' 
                      ? 'Press and hold the microphone to begin our conversation. I\'ll listen carefully and respond with both voice and text.'
                      : 'Type your message below and I\'ll respond with thoughtful, helpful information. Let\'s have a wonderful conversation.'
                    }
                  </p>
                </div>
              ) : (
                <div className="space-y-8">
                  {messages.map((message) => (
                    <div
                      key={message.id}
                      className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}
                    >
                      <div
                        className={`max-w-xs lg:max-w-md px-6 py-4 rounded-3xl ${
                          message.type === 'user'
                            ? 'bg-gradient-to-br from-amber-600 to-orange-600 text-white shadow-lg'
                            : theme === 'dark'
                            ? 'bg-warm-gray-800 text-warm-gray-100 border border-warm-gray-700 shadow-lg'
                            : 'bg-warm-gray-50 text-warm-gray-900 shadow-lg border border-warm-gray-200'
                        }`}
                      >
                        <p className="text-sm leading-relaxed font-serif">{message.text}</p>
                        <div className="flex items-center justify-between mt-3">
                          <div className="flex items-center space-x-3">
                            <span
                              className={`text-xs font-serif ${
                                message.type === 'user' 
                                  ? 'text-amber-100' 
                                  : theme === 'dark' 
                                  ? 'text-warm-gray-400' 
                                  : 'text-warm-gray-500'
                              }`}
                            >
                              {message.timestamp.toLocaleTimeString()}
                            </span>
                            {message.isVoice && (
                              <span
                                className={`text-xs px-3 py-1 rounded-full font-serif ${
                                  message.type === 'user'
                                    ? 'bg-amber-700 text-amber-100'
                                    : theme === 'dark'
                                    ? 'bg-warm-gray-700 text-warm-gray-300'
                                    : 'bg-warm-gray-200 text-warm-gray-600'
                                }`}
                              >
                                Voice
                              </span>
                            )}
                          </div>
                          {message.audioUrl && (
                            <button
                              onClick={() => handlePlayMessage(message.audioUrl!)}
                              className={`ml-3 p-2 rounded-full transition-all duration-200 ${
                                message.type === 'user' 
                                  ? 'hover:bg-amber-700' 
                                  : theme === 'dark'
                                  ? 'hover:bg-warm-gray-700'
                                  : 'hover:bg-warm-gray-200'
                              }`}
                            >
                              <Volume2 className="w-4 h-4" />
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
            <div className={`${theme === 'dark' ? 'bg-warm-gray-800 bg-opacity-90' : 'bg-warm-gray-50 bg-opacity-90'} backdrop-blur-sm border-t ${theme === 'dark' ? 'border-warm-gray-700' : 'border-warm-gray-200'} px-8 py-4`}>
              <div className="max-w-4xl mx-auto flex items-center justify-between">
                <div className="flex items-center space-x-3">
                  {chatState.status === 'processing' && (
                    <Loader2 className={`w-5 h-5 animate-spin ${theme === 'dark' ? 'text-amber-400' : 'text-amber-600'}`} />
                  )}
                  {chatState.status === 'error' && (
                    <AlertCircle className={`w-5 h-5 ${theme === 'dark' ? 'text-red-400' : 'text-red-600'}`} />
                  )}
                  {chatState.status === 'recording' && (
                    <div className="w-5 h-5 bg-red-500 rounded-full animate-pulse shadow-lg" />
                  )}
                  <span className={`text-sm font-serif font-medium ${getStatusColor()}`}>
                    {getStatusText()}
                  </span>
                </div>
                {recordingError && (
                  <span className={`text-sm font-serif ${theme === 'dark' ? 'text-red-400' : 'text-red-600'}`}>
                    {recordingError}
                  </span>
                )}
              </div>
            </div>

            {/* Input Area */}
            <div className={`${theme === 'dark' ? 'bg-warm-gray-800' : 'bg-warm-gray-50'} border-t ${theme === 'dark' ? 'border-warm-gray-700' : 'border-warm-gray-200'} px-8 py-8`}>
              <div className="max-w-4xl mx-auto">
                {/* Chat Mode Toggle */}
                <div className="flex justify-center mb-8">
                  <div className={`p-1 rounded-2xl ${theme === 'dark' ? 'bg-warm-gray-700' : 'bg-warm-gray-200'} shadow-inner`}>
                    <button
                      onClick={() => setChatMode('voice')}
                      className={`px-6 py-3 rounded-xl text-sm font-serif font-medium transition-all duration-300 ${
                        chatMode === 'voice'
                          ? 'bg-gradient-to-r from-amber-600 to-orange-600 text-white shadow-lg transform scale-105'
                          : theme === 'dark'
                          ? 'text-warm-gray-300 hover:text-white'
                          : 'text-warm-gray-600 hover:text-warm-gray-900'
                      }`}
                    >
                      <Mic className="w-4 h-4 inline mr-2" />
                      Voice Chat
                    </button>
                    <button
                      onClick={() => setChatMode('text')}
                      className={`px-6 py-3 rounded-xl text-sm font-serif font-medium transition-all duration-300 ${
                        chatMode === 'text'
                          ? 'bg-gradient-to-r from-amber-600 to-orange-600 text-white shadow-lg transform scale-105'
                          : theme === 'dark'
                          ? 'text-warm-gray-300 hover:text-white'
                          : 'text-warm-gray-600 hover:text-warm-gray-900'
                      }`}
                    >
                      <Type className="w-4 h-4 inline mr-2" />
                      Text Chat
                    </button>
                  </div>
                </div>

                {/* Input Controls */}
                {chatMode === 'voice' ? (
                  <div className="flex flex-col items-center">
                    <div>
                      <button
                        onMouseDown={handleStartRecording}
                        onMouseUp={handleStopRecording}
                        onTouchStart={handleStartRecording}
                        onTouchEnd={handleStopRecording}
                        disabled={chatState.status === 'processing'}
                        className={`
                          relative p-8 rounded-full transition-all duration-300 transform hover:scale-110 active:scale-95 shadow-2xl
                          ${
                            isRecording
                              ? 'bg-gradient-to-br from-red-500 to-red-600 hover:from-red-600 hover:to-red-700'
                              : chatState.status === 'processing'
                              ? 'bg-warm-gray-400 cursor-not-allowed'
                              : 'bg-gradient-to-br from-amber-600 to-orange-600 hover:from-amber-700 hover:to-orange-700'
                          }
                          ${isRecording ? 'animate-pulse' : ''}
                        `}
                      >
                        {chatState.status === 'processing' ? (
                          <Loader2 className="w-10 h-10 text-white animate-spin" />
                        ) : isRecording ? (
                          <MicOff className="w-10 h-10 text-white" />
                        ) : (
                          <Mic className="w-10 h-10 text-white" />
                        )}
                        {/* Recording animation */}
                        {isRecording && (
                          <div className="absolute inset-0 rounded-full border-4 border-red-300 animate-ping" />
                        )}
                      </button>
                    </div>
                    {/* Download recorded audio */}
                    {recordedAudioUrl && (
                      <a
                        href={recordedAudioUrl}
                        download="recording.wav"
                        className="mt-6 px-6 py-3 bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-700 hover:to-teal-700 text-white rounded-xl transition-all duration-300 shadow-lg font-serif font-medium"
                      >
                        Download Recording
                      </a>
                    )}
                  </div>
                ) : (
                  <div className="flex space-x-4">
                    <input
                      type="text"
                      value={textInput}
                      onChange={(e) => setTextInput(e.target.value)}
                      onKeyPress={(e) => e.key === 'Enter' && handleSendTextMessage()}
                      placeholder="Type your message here..."
                      disabled={chatState.status === 'processing'}
                      className={`flex-1 px-6 py-4 rounded-2xl border-2 ${
                        theme === 'dark'
                          ? 'bg-warm-gray-700 border-warm-gray-600 text-white placeholder-warm-gray-400'
                          : 'bg-white border-warm-gray-300 text-warm-gray-900 placeholder-warm-gray-500'
                      } focus:ring-2 focus:ring-amber-500 focus:border-transparent transition-all font-serif`}
                    />
                    <button
                      onClick={handleSendTextMessage}
                      disabled={!textInput.trim() || chatState.status === 'processing'}
                      className="px-8 py-4 bg-gradient-to-r from-amber-600 to-orange-600 hover:from-amber-700 hover:to-orange-700 disabled:from-warm-gray-400 disabled:to-warm-gray-500 text-white rounded-2xl transition-all duration-300 shadow-lg font-serif font-medium"
                    >
                      {chatState.status === 'processing' ? (
                        <Loader2 className="w-6 h-6 animate-spin" />
                      ) : (
                        <Send className="w-6 h-6" />
                      )}
                    </button>
                  </div>
                )}

                <p className={`text-center text-sm mt-6 font-serif italic ${theme === 'dark' ? 'text-warm-gray-400' : 'text-warm-gray-600'}`}>
                  {chatMode === 'voice' 
                    ? (isRecording ? 'Release to send your message' : 'Press and hold to begin recording')
                    : 'Press Enter or click send to share your thoughts'
                  }
                </p>
              </div>
            </div>
          </div>
        );
    }
  };

  return (
    <div className={`min-h-screen transition-all duration-500 ${
      theme === 'dark' 
        ? 'bg-gradient-to-br from-warm-gray-900 via-warm-gray-800 to-amber-900' 
        : 'bg-gradient-to-br from-amber-50 via-cream-50 to-orange-50'
    }`}>
      {/* Header */}
      <div className={`${theme === 'dark' ? 'bg-warm-gray-800 bg-opacity-90' : 'bg-warm-gray-50 bg-opacity-90'} backdrop-blur-sm border-b ${theme === 'dark' ? 'border-warm-gray-700' : 'border-warm-gray-200'} px-8 py-6`}>
        <div className="max-w-6xl mx-auto flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <div className="p-3 bg-gradient-to-br from-amber-200 to-orange-200 rounded-2xl shadow-lg">
              <Coffee className="w-8 h-8 text-amber-700" />
            </div>
            <div>
              <h1 className={`text-2xl font-serif font-bold ${theme === 'dark' ? 'text-warm-gray-100' : 'text-warm-gray-900'}`}>
                The Voice Assistant
              </h1>
              <p className={`text-sm font-serif italic ${theme === 'dark' ? 'text-warm-gray-400' : 'text-warm-gray-500'}`}>
                Thoughtful conversations in Vietnamese
              </p>
            </div>
          </div>
          
          <div className="flex items-center space-x-6">
            <div className="flex items-center space-x-2">
              <Sparkles className={`w-5 h-5 ${theme === 'dark' ? 'text-amber-400' : 'text-amber-600'}`} />
              <span className={`text-sm font-serif font-medium ${theme === 'dark' ? 'text-warm-gray-300' : 'text-warm-gray-700'}`}>
                AI Powered
              </span>
            </div>
            
            <button
              onClick={toggleTheme}
              className={`p-3 rounded-xl transition-all duration-300 ${
                theme === 'dark' 
                  ? 'bg-warm-gray-700 hover:bg-warm-gray-600 text-warm-gray-300' 
                  : 'bg-warm-gray-200 hover:bg-warm-gray-300 text-warm-gray-600'
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
      <div className={`${theme === 'dark' ? 'bg-warm-gray-800 bg-opacity-50' : 'bg-warm-gray-50 bg-opacity-50'} backdrop-blur-sm border-b ${theme === 'dark' ? 'border-warm-gray-700' : 'border-warm-gray-200'}`}>
        <div className="max-w-6xl mx-auto px-8">
          <nav className="flex space-x-12">
            {[
              { id: 'chat', label: 'Chat', icon: MessageCircle },
              { id: 'about', label: 'Our Story', icon: Book },
              { id: 'features', label: 'Features', icon: Sparkles },
              { id: 'contact', label: 'Contact', icon: Send },
            ].map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as ActiveTab)}
                className={`flex items-center space-x-3 py-6 border-b-3 transition-all duration-300 font-serif ${
                  activeTab === tab.id
                    ? 'border-amber-600 text-amber-600 transform scale-105'
                    : theme === 'dark'
                    ? 'border-transparent text-warm-gray-400 hover:text-warm-gray-200'
                    : 'border-transparent text-warm-gray-500 hover:text-warm-gray-700'
                }`}
              >
                <tab.icon className="w-5 h-5" />
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