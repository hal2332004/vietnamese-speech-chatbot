# Voice Chatbot System

A complete voice-enabled chatbot system that integrates Speech-to-Text (STT), Retrieval-Augmented Generation (RAG), and Text-to-Speech (TTS) APIs for seamless Vietnamese voice conversations.

## System Architecture

```
User Voice Input → STT API → RAG API → TTS API → Audio Response
```

## Features

- 🎤 **Voice Recording**: High-quality audio recording with real-time feedback
- 🗣️ **Speech Recognition**: Vietnamese speech-to-text conversion
- 🤖 **AI Chat**: Intelligent responses using RAG technology
- 🔊 **Voice Synthesis**: Natural Vietnamese text-to-speech
- 💬 **Chat History**: Full conversation history with audio playback
- 📱 **Responsive Design**: Works on desktop and mobile devices

## Prerequisites

Make sure you have the following APIs running:

1. **STT API** on `localhost:12345/stt`
2. **RAG API** on `localhost:12346/ask`
3. **TTS API** on `localhost:12347/tts`

## Installation

### Backend Setup

1. Navigate to the backend directory:
```bash
cd backend
```

2. Install Python dependencies:
```bash
pip install -r requirements.txt
```

3. Start the FastAPI server:
```bash
python main.py
```

The backend will be available at `http://localhost:8000`

### Frontend Setup

1. Install dependencies:
```bash
npm install
```

2. Start the development server:
```bash
npm run dev
```

The frontend will be available at `http://localhost:5173`

## API Endpoints

### Voice Chat
- **POST** `/chat-voice`
  - Upload audio file for complete voice interaction
  - Returns audio response with transcription headers

### Text Chat
- **POST** `/chat-text`
  - Send text question for testing
  - Returns JSON response with answer

### Health Check
- **GET** `/health`
  - Check status of all dependent services

## Usage

1. **Press and Hold** the microphone button to start recording
2. **Speak your question** in Vietnamese
3. **Release** the button to send your recording
4. **Wait** for the AI to process and respond
5. **Listen** to the audio response automatically played back

## Configuration

### Backend Configuration

Edit `backend/main.py` to change API endpoints:

```python
STT_URL = "http://localhost:12345/stt"
RAG_URL = "http://localhost:12346/ask"
TTS_URL = "http://localhost:12347/tts"
```

### Frontend Configuration

The frontend automatically connects to the backend at `http://localhost:8000`. For production, update the API URLs in `src/components/VoiceChatBot.tsx`.

## Development

### Running in Development Mode

Use the npm script to run both frontend and backend:

```bash
# Start frontend
npm run dev

# Start backend (in another terminal)
npm run backend
```

### Audio Recording Settings

The audio recorder is configured for optimal quality:
- Echo cancellation enabled
- Noise suppression enabled
- 44.1kHz sample rate
- WebM/Opus format

## Production Deployment

1. **Build the frontend**:
```bash
npm run build
```

2. **Configure CORS** in `backend/main.py` for your domain

3. **Set up proper SSL** for HTTPS (required for microphone access)

4. **Deploy both services** with proper networking configuration

## Troubleshooting

### Common Issues

1. **Microphone not working**: Ensure HTTPS is used and microphone permissions are granted
2. **API connection errors**: Verify all three APIs (STT, RAG, TTS) are running
3. **CORS errors**: Update CORS configuration in the backend
4. **Audio playback issues**: Check browser audio permissions and codec support

### Logs

Backend logs are available in the console when running the FastAPI server. Check for connection errors to the dependent APIs.

## Browser Support

- Chrome 66+
- Firefox 55+
- Safari 11+
- Edge 79+

Microphone access requires HTTPS in production environments.