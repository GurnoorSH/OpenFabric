import streamlit as st
import os
from pathlib import Path
from PIL import Image
import base64
from io import BytesIO
import json
from datetime import datetime
import logging

from core.llm import LocalLLM
from core.memory import Memory
from core.stub import Stub
from ontology_dc8f06af066e4a7880a5938933236037.config import ConfigClass

# Configure logging
logging.basicConfig(level=logging.INFO)

# Initialize session state
if 'llm' not in st.session_state:
    st.session_state.llm = LocalLLM()
if 'memory' not in st.session_state:
    st.session_state.memory = Memory()
if 'stub' not in st.session_state:
    try:
        # Initialize with proper configuration
        config = ConfigClass()
        # Use correct app IDs from documentation
        config.app_ids = [
            'c25dcd829d134ea98f5ae4dd311d13bc.node3.openfabric.network',  # Text to Image
            'f0b5f319156c4819b9827000b17e511a.node3.openfabric.network'   # Image to 3D
        ]
        # Initialize Stub with retry configuration
        st.session_state.stub = Stub(
            config.app_ids,
            max_retries=3,  # Number of retry attempts
            retry_delay=5,  # Delay between retries in seconds
            require_all_apps=False  # Allow partial initialization
        )
        
        # Check which apps are available
        available_apps = st.session_state.stub.get_available_apps()
        if len(available_apps) == len(config.app_ids):
            st.success("Successfully connected to all Openfabric services!")
        else:
            st.warning("Some Openfabric services are currently unavailable:")
            if 'c25dcd829d134ea98f5ae4dd311d13bc.node3.openfabric.network' in available_apps:
                st.success("✓ Text-to-Image service is available")
            else:
                st.error("✗ Text-to-Image service is unavailable")
            
            if 'f0b5f319156c4819b9827000b17e511a.node3.openfabric.network' in available_apps:
                st.success("✓ Image-to-3D service is available")
            else:
                st.error("✗ Image-to-3D service is unavailable")
            
            st.info("The application will continue with available services.")
    except Exception as e:
        st.error(f"Failed to initialize Openfabric services: {str(e)}")
        st.error("Please check your internet connection and try again.")
        st.error("If the problem persists, please verify your Openfabric credentials and app IDs.")
        st.stop()  # Stop the app if initialization fails

# Create directories for storing generated content
os.makedirs("generated/images", exist_ok=True)
os.makedirs("generated/models", exist_ok=True)

def save_image(image_data: bytes, prompt: str) -> str:
    """Save generated image and return the path."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"generated/images/{timestamp}_{prompt[:30]}.png"
    with open(filename, "wb") as f:
        f.write(image_data)
    return filename

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

                    # Step 2: Generate image using Openfabric Text-to-Image app
                    text_to_image_app = 'c25dcd829d134ea98f5ae4dd311d13bc.node3.openfabric.network'
                    if not st.session_state.stub.is_app_available(text_to_image_app):
                        raise Exception("Text-to-Image service is currently unavailable")
                    
                    logging.info(f"Calling Text-to-Image app with prompt: {expanded_prompt}")
                    
                    try:
                        image_response = st.session_state.stub.call(
                            text_to_image_app, 
                            {'prompt': expanded_prompt}, 
                            'super-user'
                        )
                        if not image_response:
                            raise Exception("No response received from Text-to-Image app")
                        
                        image_data = image_response.get('result')
                        if not image_data:
                            raise Exception("No image data received from Text-to-Image app")
                        
                        # Convert base64 image data to bytes if needed
                        if isinstance(image_data, str):
                            image_data = base64.b64decode(image_data)
                        
                        image_path = save_image(image_data, prompt)
                        logging.info(f"Image saved to: {image_path}")
                        
                        # Display the generated image immediately
                        st.success("Image generated successfully!")
                        display_image(image_path)
                        
                        # Step 3: Convert to 3D using Openfabric Image-to-3D app
                        image_to_3d_app = 'f0b5f319156c4819b9827000b17e511a.node3.openfabric.network'
                        if st.session_state.stub.is_app_available(image_to_3d_app):
                            logging.info("Calling Image-to-3D app")
                            
                            try:
                                model_response = st.session_state.stub.call(
                                    image_to_3d_app, 
                                    {'image': image_data}, 
                                    'super-user'
                                )
                                if not model_response:
                                    raise Exception("No response received from Image-to-3D app")
                                
                                model_data = model_response.get('result')
                                if not model_data:
                                    raise Exception("No model data received from Image-to-3D app")
                                
                                model_path = save_model(model_data, prompt)
                                logging.info(f"3D model saved to: {model_path}")
                                st.success("3D model generated successfully!")
                            except Exception as e:
                                logging.error(f"3D model generation error: {str(e)}")
                                st.warning("3D model generation failed. The image was still generated successfully.")
                        else:
                            st.warning("Image-to-3D service is currently unavailable. Only image generation is available.")

                        # Store in memory
                        embedding = st.session_state.llm.get_embedding(prompt)
                        st.session_state.memory.add_memory(
                            prompt=prompt,
                            image_path=image_path,
                            model_path=model_path if 'model_path' in locals() else None,
                            embedding=embedding
                        )

                    except Exception as e:
                        logging.error(f"Openfabric API error: {str(e)}")
                        st.error("Failed to connect to Openfabric services. Please check your internet connection and try again.")
                        st.error("If the problem persists, please verify your Openfabric credentials and app IDs.")

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

def save_model(model_data: bytes, prompt: str) -> str:
    """Save generated 3D model and return the path."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"generated/models/{timestamp}_{prompt[:30]}.glb"
    with open(filename, "wb") as f:
        f.write(model_data)
    return filename

if __name__ == "__main__":
    main() 