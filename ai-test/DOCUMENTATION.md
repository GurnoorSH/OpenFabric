# AI Creative Pipeline Documentation

## Overview
The AI Creative Pipeline is an intelligent system that transforms text prompts into stunning images and interactive 3D models using Openfabric's AI services and local LLM capabilities. This documentation provides detailed information about the system's architecture, setup, and usage.

## Authentication
The pipeline uses two simple authentication mechanisms:
1. UID (User Identifier) - Passed with each request (e.g., ?uid=super-user)
2. App IDs - UUIDs for each hosted Openfabric app, passed via the POST /config endpoint

## Table of Contents
1. [System Architecture](#system-architecture)
2. [Prerequisites](#prerequisites)
3. [Installation](#installation)
4. [Configuration](#configuration)
5. [Usage Guide](#usage-guide)
6. [API Reference](#api-reference)
7. [Troubleshooting](#troubleshooting)
8. [Development Guide](#development-guide)

## System Architecture

### Core Components

#### 1. Local LLM (Language Model)
- **Purpose**: Handles prompt understanding and expansion
- **Implementation**: Uses efficient local models for privacy and performance
- **Key Features**:
  - Prompt expansion and enhancement
  - Semantic embedding generation
  - Context-aware text processing

#### 2. Openfabric Integration
- **Services**:
  - Text-to-Image: `c25dcd829d134ea98f5ae4dd311d13bc.node3.openfabric.network`
  - Image-to-3D: `f0b5f319156c4819b9827000b17e511a.node3.openfabric.network`
- **Features**:
  - Secure WebSocket connections
  - Automatic retry mechanism
  - Error handling and recovery
  - Partial service availability support

#### 3. Memory System
- **Components**:
  - Short-term memory (session-based)
  - Long-term memory (persistent storage)
- **Features**:
  - SQLite database for storage
  - FAISS for vector similarity search
  - Automatic content organization
  - Semantic search capabilities

#### 4. File Management
- **Storage Structure**:
  ```
  generated/
  ├── images/    # Generated images
  └── models/    # Generated 3D models
  ```
- **Features**:
  - Automatic file naming
  - Timestamp-based organization
  - Efficient resource management

## Prerequisites

### System Requirements
- Python 3.8 or higher
- CUDA-capable GPU (recommended for LLM processing)
- 8GB RAM minimum (16GB recommended)
- 10GB free disk space

## Installation

### 1. Clone the Repository
```bash
git clone [repository-url]
cd ai-test
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Download LLM Model
```bash
python -c "from transformers import AutoTokenizer, AutoModel; AutoTokenizer.from_pretrained('deepseek-ai/deepseek-coder-6.7b-base'); AutoModel.from_pretrained('deepseek-ai/deepseek-coder-6.7b-base')"
```

## Configuration

### 1. Openfabric Configuration
Update `config/state.json`:
```json
{
  "super-user": {
    "app_ids": [
      "f0997a01-d6d3-a5fe-53d8-561300318557",
      "69543f29-4d41-4afc-7f29-3d51591f11eb"
    ]
  }
}
```

### 2. Environment Variables
Create `.env` file:
```env
LLM_MODEL_PATH=path_to_your_model
STORAGE_PATH=custom_storage_path
```

## Usage Guide

### 1. Starting the Application
```bash
python app/streamlit_app.py
```
Access the web interface at `http://localhost:8501`

### 2. Text-to-Image Generation
1. Enter a descriptive prompt
2. The system will:
   - Expand and enhance your prompt
   - Generate an image
   - Display the result
   - Save to the images directory

### 3. Image-to-3D Conversion
1. After image generation:
   - The system automatically converts the image to 3D
   - Saves the model in GLB format
   - Provides interactive 3D viewer

### 4. Memory and History
- Access previous generations
- Search through creation history
- View similar creations

## API Reference

### Core Classes

#### Stub Class
```python
class Stub:
    def __init__(self, app_ids: List[str], max_retries: int = 3, 
                 retry_delay: int = 5, require_all_apps: bool = False)
    def call(self, app_id: str, data: Dict, user_id: str) -> Dict
    def is_app_available(self, app_id: str) -> bool
    def get_available_apps(self) -> List[str]
```

#### Memory Class
```python
class Memory:
    def __init__(self, db_path: str = "memory.db")
    def add_memory(self, prompt: str, image_path: Optional[str] = None,
                  model_path: Optional[str] = None, embedding: Optional[np.ndarray] = None)
    def search_similar(self, embedding: np.ndarray) -> List[Dict]
```

## Troubleshooting

### Common Issues

1. **Service Connection Errors**
   - Check internet connection
   - Verify Openfabric API key
   - Ensure app IDs are correct
   - Check service availability

2. **LLM Processing Issues**
   - Verify GPU availability
   - Check model installation
   - Monitor memory usage

3. **File System Errors**
   - Check disk space
   - Verify directory permissions
   - Ensure proper file paths

### Error Messages

1. **"Failed to initialize Openfabric services"**
   - Check network connection
   - Verify API credentials
   - Ensure service availability

2. **"No response received from service"**
   - Check service status
   - Verify input parameters
   - Retry the operation

## Development Guide

### Project Structure
```
ai-test/
├── app/
│   ├── core/
│   │   ├── llm.py         # LLM integration
│   │   ├── memory.py      # Memory management
│   │   ├── remote.py      # Network communication
│   │   └── stub.py        # Openfabric SDK
│   ├── config/
│   │   ├── state.json     # App configuration
│   │   └── properties.json
│   ├── generated/
│   │   ├── images/
│   │   └── models/
│   ├── streamlit_app.py   # Web interface
│   └── main.py           # Core logic
├── requirements.txt
└── DOCUMENTATION.md
```

### Adding New Features

1. **New Service Integration**
   - Add service ID to configuration
   - Implement service interface
   - Update error handling

2. **UI Enhancements**
   - Modify streamlit_app.py
   - Add new components
   - Update documentation

3. **Memory System Extensions**
   - Add new storage types
   - Implement new search methods
   - Update database schema

### Best Practices

1. **Code Style**
   - Follow PEP 8 guidelines
   - Use type hints
   - Document functions

2. **Error Handling**
   - Implement proper logging
   - Use try-except blocks
   - Provide user feedback

3. **Testing**
   - Write unit tests
   - Test edge cases
   - Verify error handling


## Support and Contact
{
  "app_ids": [
    "f0997a01-d6d3-a5fe-53d8-561300318557",
    "69543f29-4d41-4afc-7f29-3d51591f11eb"
  ]
}

super-user


For support and questions:
- Open an issue on GitHub
- Contact the development team
- Check the Openfabric documentation

## License

This project is licensed under the MIT License - see the LICENSE file for details. 