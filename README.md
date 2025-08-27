# Vietnamese Speech Chatbox

This project is a Vietnamese speech chatbox system that integrates speech-to-text (STT), text-to-speech (TTS), and conversational AI capabilities. It is designed to facilitate natural, real-time voice conversations in Vietnamese, making it suitable for educational, accessibility, and interactive applications.

## GitHub Repository

```bash
https://github.com/hal2332004/vietnamese-speech-chatbot.git
```

## Features

- **Speech-to-Text (STT):** Converts spoken Vietnamese into text using advanced models.
- **Text-to-Speech (TTS):** Synthesizes natural-sounding Vietnamese speech from text.
- **Conversational AI:** Integrates with large language models for intelligent dialogue using llama.cpp.
- **Local Model Support:** Run Vietnamese language models locally with CUDA acceleration.
- **Modular Backend:** Easily extendable and customizable for different use cases.
- **User Interface:** (Located in `src/UI/`) for interactive chat experiences.

## Project Structure

```
vietnamese-speech-chatbox/
├── data/                # Datasets and resources
├── src/
│   ├── backend/         # Backend scripts and models
│   ├── llama.cpp/       # LLM integration (Llama.cpp)
│   └── UI/              # User interface code
├── requirements.txt     # Python dependencies
└── README.md            # Project documentation
```

## Getting Started

### Prerequisites

- Python 3.8+
- Node.js (for UI)
- CMake 3.14+
- CUDA Toolkit (for GPU acceleration)
- Git
- wget or curl

### Installation

1. **Install PyTorch with CUDA Support:**
   ```bash
   pip install torch==2.6.0 torchvision==0.21.0 torchaudio==2.6.0 --index-url https://download.pytorch.org/whl/cu126
   ```

2. **Clone the repository:**
   ```bash
   git clone -b features/orinx --single-branch https://github.com/hal2332004/vietnamese-speech-chatbot.git
   cd vietnamese-speech-chatbox
   ```

3. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up Llama.cpp with CUDA Support:**
   ```bash
   # Build llama.cpp with CUDA acceleration
   cmake -B build -DGGML_CUDA=on 
   cmake --build build --config Release -j4
   ```

5. **Download Vietnamese Language Model:**
   
   Choose one of the following methods:
   
   **Option A: Using wget**
   ```bash
   wget https://huggingface.co/mradermacher/Vi-Qwen2-3B-RAG-GGUF/resolve/main/Vi-Qwen2-3B-RAG.Q8_0.gguf
   ```
   
   **Option B: Using curl**
   ```bash
   curl -L -o Vi-Qwen2-3B-RAG.Q8_0.gguf https://huggingface.co/mradermacher/Vi-Qwen2-3B-RAG-GGUF/resolve/main/Vi-Qwen2-3B-RAG.Q8_0.gguf
   ```
   
   Model source: [Vi-Qwen2-3B-RAG-GGUF](https://huggingface.co/mradermacher/Vi-Qwen2-3B-RAG-GGUF/tree/main)

6. **Install UI dependencies:**
   ```bash
   cd src/UI
   npm install
   ```

## Usage

### Starting the Local Language Model Server

Before running the backend, start the llama.cpp server with the Vietnamese model:

```bash
./llama-server -m Vi-Qwen2-3B-RAG.Q8_0.gguf -ngl -1
```

**Parameters:**
- `-m`: Path to the model file
- `-ngl -1`: Use GPU acceleration (offload all layers to GPU)

### Running the Backend

```bash
cd src/backend
python main.py
```

### Running the UI

```bash
cd src/UI
npm run dev
```

## Model Information

- **Model:** Vi-Qwen2-3B-RAG (Vietnamese)
- **Size:** ~3B parameters
- **Format:** GGUF (Q8_0 quantization)
- **Features:** Optimized for Vietnamese language understanding and generation
- **Hardware:** Supports CUDA acceleration for faster inference

## Data

Place your datasets in the `data/` directory. See `data/download.txt` for download instructions and `data/Giáo trình môn học FPT 2 - syllabus_data_format.csv` for data format examples.

## Troubleshooting

### Build Issues
- Ensure CUDA Toolkit is properly installed
- Check CMake version (3.14+ required)
- Verify compiler compatibility with CUDA

### Model Loading Issues
- Check available GPU memory
- Ensure model file is completely downloaded
- Try reducing `-ngl` value if GPU memory is insufficient

## Contributing

Contributions are welcome! Please open issues or pull requests for suggestions and improvements.

## License

This project is licensed under the MIT License.
