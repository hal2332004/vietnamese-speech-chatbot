import React, { useState, useRef, useEffect } from 'react';
import { Mic, MicOff, Send, Volume2, Loader2, MessageCircle, Zap, AlertCircle } from 'lucide-react';
import { useAudioRecorder } from '../hooks/useAudioRecorder';

interface ChatMessage {
  id: string;
  type: 'user' | 'bot';
  text: string;
  timestamp: Date;
  audioUrl?: string;
}

interface ChatState {
  status: 'idle' | 'recording' | 'processing' | 'playing' | 'error';
  error?: string;
}

const VoiceChatBot: React.FC = () => {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [chatState, setChatState] = useState<ChatState>({ status: 'idle' });
  const [isPlaying, setIsPlaying] = useState(false);
  
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
    switch (chatState.status) {
      case 'recording':
        return 'text-red-600';
      case 'processing':
        return 'text-blue-600';
      case 'playing':
        return 'text-green-600';
      case 'error':
        return 'text-red-600';
      default:
        return 'text-gray-600';
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-indigo-50 flex flex-col">
      {/* Header */}
      <div className="bg-white/80 backdrop-blur-sm border-b border-gray-200 px-6 py-4">
        <div className="max-w-4xl mx-auto flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-blue-100 rounded-lg">
              <MessageCircle className="w-6 h-6 text-blue-600" />
            </div>
            <div>
              <h1 className="text-xl font-semibold text-gray-900">Voice Assistant</h1>
              <p className="text-sm text-gray-500">Speak naturally in Vietnamese</p>
            </div>
          </div>
          <div className="flex items-center space-x-2">
            <Zap className="w-4 h-4 text-green-500" />
            <span className="text-sm font-medium text-gray-700">AI Powered</span>
          </div>
        </div>
      </div>

      {/* Chat Messages */}
      <div className="flex-1 max-w-4xl mx-auto w-full px-6 py-8 overflow-y-auto">
        {messages.length === 0 ? (
          <div className="text-center py-12">
            <div className="p-4 bg-blue-100 rounded-full w-16 h-16 mx-auto mb-4 flex items-center justify-center">
              <Mic className="w-8 h-8 text-blue-600" />
            </div>
            <h3 className="text-lg font-medium text-gray-900 mb-2">Start a conversation</h3>
            <p className="text-gray-600 max-w-md mx-auto">
              Press and hold the microphone button to record your question. 
              I'll listen, understand, and respond with both text and voice.
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
                      : 'bg-white text-gray-900 shadow-md border border-gray-100'
                  }`}
                >
                  <p className="text-sm leading-relaxed">{message.text}</p>
                  <div className="flex items-center justify-between mt-2">
                    <span
                      className={`text-xs ${
                        message.type === 'user' ? 'text-blue-100' : 'text-gray-500'
                      }`}
                    >
                      {message.timestamp.toLocaleTimeString()}
                    </span>
                    {message.audioUrl && (
                      <button
                        onClick={() => handlePlayMessage(message.audioUrl!)}
                        className={`ml-2 p-1 rounded-full hover:bg-gray-100 transition-colors ${
                          message.type === 'user' ? 'hover:bg-blue-700' : ''
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
      <div className="bg-white/90 backdrop-blur-sm border-t border-gray-200 px-6 py-3">
        <div className="max-w-4xl mx-auto flex items-center justify-between">
          <div className="flex items-center space-x-2">
            {chatState.status === 'processing' && (
              <Loader2 className="w-4 h-4 animate-spin text-blue-600" />
            )}
            {chatState.status === 'error' && (
              <AlertCircle className="w-4 h-4 text-red-600" />
            )}
            {chatState.status === 'recording' && (
              <div className="w-4 h-4 bg-red-600 rounded-full animate-pulse" />
            )}
            <span className={`text-sm font-medium ${getStatusColor()}`}>
              {getStatusText()}
            </span>
          </div>
          {recordingError && (
            <span className="text-sm text-red-600">{recordingError}</span>
          )}
        </div>
      </div>

      {/* Voice Control */}
      <div className="bg-white border-t border-gray-200 px-6 py-6">
        <div className="max-w-4xl mx-auto flex justify-center">
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
        <p className="text-center text-sm text-gray-600 mt-4">
          {isRecording ? 'Release to send' : 'Press and hold to record'}
        </p>
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