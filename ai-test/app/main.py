import logging
import os
from typing import Dict
from datetime import datetime
from pathlib import Path

from ontology_dc8f06af066e4a7880a5938933236037.config import ConfigClass
from ontology_dc8f06af066e4a7880a5938933236037.input import InputClass
from ontology_dc8f06af066e4a7880a5938933236037.output import OutputClass
from openfabric_pysdk.context import AppModel, State
from core.stub import Stub
from core.llm import LocalLLM
from core.memory import Memory

# Configurations for the app
configurations: Dict[str, ConfigClass] = dict()

# Initialize LLM and Memory
llm = LocalLLM()
memory = Memory()

# Create directories for storing generated content
os.makedirs("generated/images", exist_ok=True)
os.makedirs("generated/models", exist_ok=True)

############################################################
# Config callback function
############################################################
def config(configuration: Dict[str, ConfigClass], state: State) -> None:
    """
    Stores user-specific configuration data.

    Args:
        configuration (Dict[str, ConfigClass]): A mapping of user IDs to configuration objects.
        state (State): The current state of the application (not used in this implementation).
    """
    for uid, conf in configuration.items():
        logging.info(f"Saving new config for user with id:'{uid}'")
        configurations[uid] = conf

def save_image(image_data: bytes, prompt: str) -> str:
    """Save generated image and return the path."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"generated/images/{timestamp}_{prompt[:30]}.png"
    with open(filename, "wb") as f:
        f.write(image_data)
    return filename

def save_model(model_data: bytes, prompt: str) -> str:
    """Save generated 3D model and return the path."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"generated/models/{timestamp}_{prompt[:30]}.glb"
    with open(filename, "wb") as f:
        f.write(model_data)
    return filename

############################################################
# Execution callback function
############################################################
def execute(model: AppModel) -> None:
    """
    Main execution entry point for handling a model pass.

    Args:
        model (AppModel): The model object containing request and response structures.
    """
    # Retrieve input
    request: InputClass = model.request

    # Retrieve user config
    user_config: ConfigClass = configurations.get('super-user', None)
    logging.info(f"{configurations}")

    # Initialize the Stub with app IDs
    app_ids = user_config.app_ids if user_config else []
    stub = Stub(app_ids)

    try:
        # Step 1: Expand prompt using LLM
        expanded_prompt = llm.expand_prompt(request.prompt)
        logging.info(f"Expanded prompt: {expanded_prompt}")

        # Step 2: Generate image using Text-to-Image app
        text_to_image_app = 'f0997a01-d6d3-a5fe-53d8-561300318557'
        image_response = stub.call(text_to_image_app, {'prompt': expanded_prompt}, 'super-user')
        image_data = image_response.get('result')
        image_path = save_image(image_data, request.prompt)

        # Step 3: Convert to 3D using Image-to-3D app
        image_to_3d_app = '69543f29-4d41-4afc-7f29-3d51591f11eb'
        model_response = stub.call(image_to_3d_app, {'image': image_data}, 'super-user')
        model_data = model_response.get('result')
        model_path = save_model(model_data, request.prompt)

        # Store in memory
        embedding = llm.get_embedding(request.prompt)
        memory.add_memory(
            prompt=request.prompt,
            image_path=image_path,
            model_path=model_path,
            embedding=embedding
        )

        # Prepare response
        response: OutputClass = model.response
        response.message = f"Successfully generated image and 3D model from prompt: {request.prompt}"
        
        # Add paths to response
        response.image_path = image_path
        response.model_path = model_path

    except Exception as e:
        logging.error(f"Error processing request: {str(e)}")
        response: OutputClass = model.response
        response.message = f"Error: {str(e)}"