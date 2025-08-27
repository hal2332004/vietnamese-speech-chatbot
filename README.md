# Vietnamese Speech Chatbox

This project is a Vietnamese speech chatbox system that integrates speech-to-text (STT), text-to-speech (TTS), and conversational AI capabilities. It is designed to facilitate natural, real-time voice conversations in Vietnamese, making it suitable for educational, accessibility, and interactive applications.

## Features

- **Speech-to-Text (STT):** Converts spoken Vietnamese into text using advanced models.
- **Text-to-Speech (TTS):** Synthesizes natural-sounding Vietnamese speech from text.
- **Conversational AI:** Integrates with large language models for intelligent dialogue.
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
├── tsconfig.json        # TypeScript config (for UI)
└── README.md            # Project documentation
```

## Getting Started

### Prerequisites

- Python 3.8+
- Node.js (for UI)
- CUDA (optional, for GPU acceleration)

### Installation

1. **Clone the repository:**
   ```bash
   git clone <repo-url>
   cd vietnamese-speech-chatbox
   ```
2. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
3. **(Optional) Set up Llama.cpp:**
   - See `src/llama.cpp/README.md` for instructions.
4. **Install UI dependencies:**
   ```bash
   cd src/UI
   npm install
   ```

## Usage

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

## Data

Place your datasets in the `data/` directory. See `data/download.txt` for download instructions and `data/Giáo trình môn học FPT 2 - syllabus_data_format.csv` for data format examples.

## Contributing

Contributions are welcome! Please open issues or pull requests for suggestions and improvements.

## License

This project is licensed under the MIT License.
