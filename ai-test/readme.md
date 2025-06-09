# 🎨 AI Creative Pipeline

A powerful end-to-end pipeline that transforms text prompts into stunning images and interactive 3D models using Openfabric's AI services and local LLM capabilities.

## 🌟 Features

- **Text-to-Image Generation**: Convert text descriptions into high-quality images
- **Image-to-3D Conversion**: Transform 2D images into interactive 3D models
- **Local LLM Integration**: Uses local language models for prompt understanding and expansion
- **Memory System**: Maintains both short-term and long-term memory of generated content
- **User-Friendly Interface**: Streamlit-based web interface for easy interaction

## 🛠️ Technical Architecture

### Core Components

1. **Local LLM (Language Model)**
   - Handles prompt understanding and expansion
   - Generates embeddings for memory retrieval
   - Uses efficient local models for privacy and performance

2. **Openfabric Integration**
   - Text-to-Image App: `c25dcd829d134ea98f5ae4dd311d13bc.node3.openfabric.network`
   - Image-to-3D App: `f0b5f319156c4819b9827000b17e511a.node3.openfabric.network`
   - Secure WebSocket connections for real-time communication

3. **Memory System**
   - Short-term: Session-based context management
   - Long-term: Persistent storage of generated content
   - Semantic search capabilities for content retrieval

4. **File Management**
   - Organized storage of generated images and 3D models
   - Automatic file naming and organization
   - Efficient resource management

## 🚀 Getting Started

### Prerequisites

- Python 3.8 or higher
- Openfabric account and API access
- Local LLM setup (DeepSeek or Llama)

### Installation

1. Clone the repository:
   ```bash
   git clone [repository-url]
   cd ai-test
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Configure Openfabric:
   - Update `config/state.json` with your Openfabric app IDs
   - Ensure proper authentication is set up

### Running the Application

1. Start the application:
   ```bash
   python app/streamlit_app.py
   ```

2. Access the web interface:
   - Open your browser and navigate to `http://localhost:8501`

## 💡 Usage Guide

1. **Text Prompt Input**
   - Enter a descriptive text prompt
   - The system will automatically expand and enhance your prompt

2. **Image Generation**
   - The system generates an image based on your prompt
   - View and download the generated image

3. **3D Model Creation**
   - The generated image is automatically converted to a 3D model
   - Interactive 3D viewer available in the interface

4. **Memory and History**
   - Access previously generated content
   - Search through your creation history
   - Reference past generations for new creations

## 🔧 Configuration

### App Configuration

The application can be configured through `config/state.json`:

```json
{
  "super-user": {
    "app_ids": [
      "c25dcd829d134ea98f5ae4dd311d13bc.node3.openfabric.network",
      "f0b5f319156c4819b9827000b17e511a.node3.openfabric.network"
    ]
  }
}
```

### Environment Variables

- `OPENFABRIC_API_KEY`: Your Openfabric API key
- `LLM_MODEL_PATH`: Path to your local LLM model
- `STORAGE_PATH`: Custom storage location for generated content

## 📁 Project Structure

```
ai-test/
├── app/
│   ├── core/
│   │   ├── llm.py
│   │   ├── memory.py
│   │   ├── remote.py
│   │   └── stub.py
│   ├── config/
│   │   ├── state.json
│   │   └── properties.json
│   ├── generated/
│   │   ├── images/
│   │   └── models/
│   ├── streamlit_app.py
│   └── main.py
├── requirements.txt
└── readme.md
```

## 🔒 Security Considerations

- All API keys and sensitive data are stored securely
- Local LLM processing ensures data privacy
- Secure WebSocket connections for Openfabric communication
- Input validation and sanitization

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- Openfabric for providing the AI services
- The open-source community for various tools and libraries
- Contributors and maintainers of the project