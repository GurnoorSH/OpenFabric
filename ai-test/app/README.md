# AI Creative Partner

An intelligent pipeline that transforms text prompts into stunning visuals and 3D models using Openfabric and local LLMs.

## Features

- 🤖 Local LLM integration for prompt understanding and expansion
- 🎨 Text-to-Image generation using Openfabric
- 🎮 Image-to-3D model conversion using Openfabric
- 💾 Persistent memory with similarity search
- 🖥️ Beautiful Streamlit interface

## Prerequisites

- Python 3.8 or higher
- Poetry for dependency management
- CUDA-capable GPU (recommended for faster LLM processing)

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd ai-test
```

2. Install dependencies using Poetry:
```bash
poetry install
```

3. Download the required LLM model:
```bash
poetry run python -c "from transformers import AutoTokenizer, AutoModel; AutoTokenizer.from_pretrained('deepseek-ai/deepseek-coder-6.7b-base'); AutoModel.from_pretrained('deepseek-ai/deepseek-coder-6.7b-base')"
```

## Running the Application

### Option 1: Using start.sh

```bash
./start.sh
```

### Option 2: Using Docker

```bash
docker build -t ai-creative-partner .
docker run -p 8888:8888 ai-creative-partner
```

### Option 3: Running Streamlit Interface

```bash
poetry run streamlit run streamlit_app.py
```

## Usage

1. Access the application at `http://localhost:8888/swagger-ui/#/App/post_execution`
2. Enter your creative prompt (e.g., "Make me a glowing dragon standing on a cliff at sunset")
3. The system will:
   - Expand your prompt using the local LLM
   - Generate an image using Openfabric's Text-to-Image app
   - Convert the image to a 3D model using Openfabric's Image-to-3D app
   - Store the results in memory for future reference

## Project Structure

```
ai-test/
├── app/
│   ├── core/
│   │   ├── llm.py         # Local LLM integration
│   │   ├── memory.py      # Memory management
│   │   └── stub.py        # Openfabric SDK integration
│   ├── generated/
│   │   ├── images/        # Generated images
│   │   └── models/        # Generated 3D models
│   ├── main.py            # Main application logic
│   ├── streamlit_app.py   # Streamlit interface
│   └── README.md
├── pyproject.toml         # Dependencies
└── Dockerfile            # Docker configuration
```

## Memory System

The application implements a two-tier memory system:

1. **Short-Term Memory**: Maintains context during a single interaction
2. **Long-Term Memory**: Persists across sessions using SQLite and FAISS for vector similarity search

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details. 