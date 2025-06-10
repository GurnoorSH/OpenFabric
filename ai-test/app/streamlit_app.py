import streamlit as st
import os
from pathlib import Path
from PIL import Image
import base64
from io import BytesIO
import json
from datetime import datetime
import logging
import re
import requests
import asyncio
import nest_asyncio

from core.llm import LocalLLM
from core.memory import Memory
from core.stub import Stub
from ontology_dc8f06af066e4a7880a5938933236037.config import ConfigClass

# Configure logging
logging.basicConfig(level=logging.INFO)

# Apply nest_asyncio to allow nested event loops
nest_asyncio.apply()

# Initialize Stub with app IDs
TEXT_TO_IMAGE_APP = 'f0997a01-d6d3-a5fe-53d8-561300318557'
IMAGE_TO_3D_APP = '69543f29-4d41-4afc-7f29-3d51591f11eb'
stub = Stub([TEXT_TO_IMAGE_APP, IMAGE_TO_3D_APP], max_retries=3, retry_delay=1, require_all_apps=False)

# Initialize service status
service_status = {
    TEXT_TO_IMAGE_APP: False,
    IMAGE_TO_3D_APP: False
}

def initialize_services():
    """Initialize services and update their status."""
    try:
        # Try to initialize Text-to-Image service
        if stub._initialize_app(TEXT_TO_IMAGE_APP):
            service_status[TEXT_TO_IMAGE_APP] = True
            logging.info(f"Text-to-Image service initialized successfully")
        
        # Try to initialize Image-to-3D service
        if stub._initialize_app(IMAGE_TO_3D_APP):
            service_status[IMAGE_TO_3D_APP] = True
            logging.info(f"Image-to-3D service initialized successfully")
    except Exception as e:
        logging.error(f"Error initializing services: {str(e)}")

# Initialize services in the background
initialize_services()

def sanitize_filename(filename: str) -> str:
    """Sanitize filename by removing invalid characters."""
    # Remove invalid characters and replace spaces with underscores
    sanitized = re.sub(r'[<>:"/\\|?*\n\r\t]', '', filename)
    sanitized = sanitized.replace(' ', '_')
    # Limit length and ensure it's not empty
    return sanitized[:50] if sanitized else "untitled"

def save_image(image_data: bytes, prompt: str) -> str:
    """Save generated image and return the path."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_prompt = sanitize_filename(prompt)
    filename = f"generated/images/{timestamp}_{safe_prompt}.png"
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    with open(filename, "wb") as f:
        f.write(image_data)
    return filename

def save_model(model_data: bytes, prompt: str) -> str:
    """Save generated 3D model and return the path."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_prompt = sanitize_filename(prompt)
    filename = f"generated/models/{timestamp}_{safe_prompt}.glb"
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    with open(filename, "wb") as f:
        f.write(model_data)
    return filename

def call_text_to_image(prompt: str) -> bytes:
    """Call the Text-to-Image service using Stub."""
    try:
        # Create a new event loop for this call
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        logging.info(f"Calling Text-to-Image service with prompt: {prompt}")
        response = stub.call(TEXT_TO_IMAGE_APP, {'prompt': prompt}, 'super-user')
        if not response or 'result' not in response:
            raise ValueError("Invalid response format")
        return base64.b64decode(response['result'])
    except Exception as e:
        logging.error(f"Text-to-Image API error: {str(e)}")
        st.error(f"Text-to-Image API error: {str(e)}")
        raise
    finally:
        loop.close()

def call_image_to_3d(image_data: bytes) -> bytes:
    """Call the Image-to-3D service using Stub."""
    try:
        # Create a new event loop for this call
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # Convert image to base64
        image_b64 = base64.b64encode(image_data).decode('utf-8')
        logging.info("Calling Image-to-3D service")
        response = stub.call(IMAGE_TO_3D_APP, {'image': image_b64}, 'super-user')
        if not response or 'result' not in response:
            raise ValueError("Invalid response format")
        return base64.b64decode(response['result'])
    except Exception as e:
        logging.error(f"Image-to-3D API error: {str(e)}")
        st.error(f"Image-to-3D API error: {str(e)}")
        raise
    finally:
        loop.close()

# Initialize session state
if 'llm' not in st.session_state:
    st.session_state.llm = LocalLLM()
if 'memory' not in st.session_state:
    st.session_state.memory = Memory()

def display_image(image_path: str):
    """Display an image in the Streamlit interface."""
    try:
        if os.path.exists(image_path):
            image = Image.open(image_path)
            st.image(image, caption="Generated Image", use_container_width=True)
        else:
            st.error(f"Image not found at {image_path}")
    except Exception as e:
        st.error(f"Error displaying image: {str(e)}")
        logging.error(f"Error displaying image: {str(e)}")

def main():
    st.title("🎨 AI Creative Image-3D Generator")
    st.write("Transform your ideas into stunning visuals and 3D models!")

    # Show current configuration and service status
    st.sidebar.header("Configuration")
    st.sidebar.write("Text-to-Image App ID:", TEXT_TO_IMAGE_APP)
    st.sidebar.write("Image-to-3D App ID:", IMAGE_TO_3D_APP)
    st.sidebar.write("User ID: super-user")
    
    # Show service status
    st.sidebar.header("Service Status")
    st.sidebar.write("Text-to-Image Service:", "✅ Available" if service_status[TEXT_TO_IMAGE_APP] else "❌ Unavailable")
    st.sidebar.write("Image-to-3D Service:", "✅ Available" if service_status[IMAGE_TO_3D_APP] else "❌ Unavailable")
    
    if not service_status[TEXT_TO_IMAGE_APP]:
        st.error("Text-to-Image service is currently unavailable. Please try again later.")
        return

    # Input section
    prompt = st.text_area("Enter your creative idea:", 
                         placeholder="e.g., 'Make me a glowing dragon standing on a cliff at sunset'")
    
    if st.button("Generate"):
        if prompt:
            with st.spinner("Processing your request..."):
                try:
                    # Step 1: Expand prompt using LLM
                    expanded_prompt = st.session_state.llm.expand_prompt(prompt)
                    st.write("Expanded Description:", expanded_prompt)

                    # Step 2: Generate image using Text-to-Image service
                    try:
                        image_data = call_text_to_image(expanded_prompt)
                        image_path = save_image(image_data, prompt)
                        logging.info(f"Image saved to: {image_path}")
                        
                        # Display the generated image immediately
                        st.success("Image generated successfully!")
                        display_image(image_path)
                        
                        # Step 3: Convert to 3D using Image-to-3D service (only if available)
                        if service_status[IMAGE_TO_3D_APP]:
                            try:
                                model_data = call_image_to_3d(image_data)
                                model_path = save_model(model_data, prompt)
                                logging.info(f"3D model saved to: {model_path}")
                                st.success("3D model generated successfully!")
                            except Exception as e:
                                logging.error(f"3D model generation error: {str(e)}")
                                st.warning("3D model generation failed. The image was still generated successfully.")
                        else:
                            st.info("3D model generation is currently unavailable. Only image generation is active.")

                        # Store in memory
                        embedding = st.session_state.llm.get_embedding(prompt)
                        st.session_state.memory.add_memory(
                            prompt=prompt,
                            image_path=image_path,
                            model_path=model_path if 'model_path' in locals() else None,
                            embedding=embedding
                        )

                    except Exception as e:
                        logging.error(f"Image generation error: {str(e)}")
                        st.error(f"Image generation error: {str(e)}")
                        st.error("Please check the logs for more details.")

                except Exception as e:
                    logging.error(f"Error during generation: {str(e)}")
                    st.error(f"Error during generation: {str(e)}")
                    st.error("Please try again with a different prompt.")

    # Memory section
    st.header("🎯 Similar Creations")
    if prompt:
        similar_memories = st.session_state.memory.search_similar(
            st.session_state.llm.get_embedding(prompt)
        )
        if similar_memories:
            for memory in similar_memories:
                with st.expander(f"Similar creation from {memory['created_at']}"):
                    st.write("Prompt:", memory['prompt'])
                    if memory['image_path'] and os.path.exists(memory['image_path']):
                        display_image(memory['image_path'])

if __name__ == "__main__":
    main() 