import json
import logging
import pprint
import time
from typing import Any, Dict, List, Literal, Tuple, Optional

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from core.remote import Remote
from openfabric_pysdk.helper import has_resource_fields, json_schema_to_marshmallow, resolve_resources
from openfabric_pysdk.loader import OutputSchemaInst

# Type aliases for clarity
Manifests = Dict[str, dict]
Schemas = Dict[str, Tuple[dict, dict]]
Connections = Dict[str, Remote]


class Stub:
    """
    Stub acts as a lightweight client interface that initializes remote connections
    to multiple Openfabric applications, fetching their manifests, schemas, and enabling
    execution of calls to these apps.

    Attributes:
        _schema (Schemas): Stores input/output schemas for each app ID.
        _manifest (Manifests): Stores manifest metadata for each app ID.
        _connections (Connections): Stores active Remote connections for each app ID.
    """

    # ----------------------------------------------------------------------
    def __init__(self, app_ids: List[str], max_retries: int = 3, retry_delay: int = 5, require_all_apps: bool = False):
        """
        Initialize the Stub with Openfabric app IDs and retry configuration.
        
        Args:
            app_ids: List of Openfabric app IDs
            max_retries: Maximum number of retry attempts
            retry_delay: Delay between retries in seconds
            require_all_apps: Whether to require all apps to be available
        """
        self._schema: Schemas = {}
        self._manifest: Manifests = {}
        self._connections: Connections = {}
        self.app_ids = app_ids
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.require_all_apps = require_all_apps
        self.initialized_apps = set()
        self.failed_apps = set()
        
        # Configure session with retry strategy
        self.session = requests.Session()
        retry_strategy = Retry(
            total=max_retries,
            backoff_factor=retry_delay,
            status_forcelist=[500, 502, 503, 504],
            allowed_methods=["GET", "POST"]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        # Initialize apps
        self._initialize_apps()

    def _initialize_apps(self):
        """Initialize all apps and track their status."""
        for app_id in self.app_ids:
            try:
                self._initialize_app(app_id)
            except Exception as e:
                logging.error(f"Failed to initialize app {app_id}: {str(e)}")
                self.failed_apps.add(app_id)
                if self.require_all_apps:
                    raise Exception(f"Required app {app_id} failed to initialize")
        
        if self.failed_apps:
            logging.warning(f"The following apps failed to initialize: {' '.join(self.failed_apps)}")
        if self.initialized_apps:
            logging.info(f"Successfully initialized apps: {' '.join(self.initialized_apps)}")
    
    def _initialize_app(self, app_id: str):
        """Initialize a single app with retry logic."""
        manifest_url = f"https://{app_id}/manifest"
        
        for attempt in range(self.max_retries):
            try:
                logging.info(f"[{app_id}] Fetching manifest from: {manifest_url}")
                response = self.session.get(manifest_url, timeout=10)
                response.raise_for_status()
                
                # Validate manifest
                manifest = response.json()
                if not manifest or not isinstance(manifest, dict):
                    raise ValueError("Invalid manifest format")
                
                self.initialized_apps.add(app_id)
                logging.info(f"[{app_id}] Successfully initialized")
                return
                
            except requests.exceptions.RequestException as e:
                if attempt < self.max_retries - 1:
                    logging.warning(f"[{app_id}] Attempt {attempt + 1} failed: {str(e)}. Retrying in {self.retry_delay} seconds...")
                    time.sleep(self.retry_delay)
                else:
                    raise Exception(f"Network error while connecting to {app_id} after {self.max_retries} attempts: {str(e)}")
            except Exception as e:
                raise Exception(f"Error initializing app {app_id}: {str(e)}")

    # ----------------------------------------------------------------------
    def call(self, app_id: str, data: Any, uid: str = 'super-user') -> dict:
        """
        Call an Openfabric app with retry logic.
        
        Args:
            app_id: The app ID to call
            data: The data to send to the app
            uid: The user ID making the request (defaults to 'super-user')
            
        Returns:
            Dict containing the app's response
            
        Raises:
            Exception if the app is not available or the call fails
        """
        if not self.is_app_available(app_id):
            raise Exception(f"App {app_id} is not available")
        
        api_url = f"https://{app_id}/api"
        full_url = f"{api_url}?uid={uid}"
        
        logging.info(f"Making API call to: {full_url}")
        logging.info(f"Request data: {json.dumps(data, indent=2)}")
        
        for attempt in range(self.max_retries):
            try:
                # Add UID as a query parameter
                response = self.session.post(
                    full_url,
                    json=data,
                    timeout=30
                )
                response.raise_for_status()
                
                result = response.json()
                logging.info(f"Response from {app_id}: {json.dumps(result, indent=2)}")
                
                if not result or not isinstance(result, dict):
                    raise ValueError("Invalid response format")
                
                return result
                
            except requests.exceptions.RequestException as e:
                if attempt < self.max_retries - 1:
                    logging.warning(f"[{app_id}] API call attempt {attempt + 1} failed: {str(e)}. Retrying in {self.retry_delay} seconds...")
                    time.sleep(self.retry_delay)
                else:
                    raise Exception(f"Failed to call app {app_id} after {self.max_retries} attempts: {str(e)}")
            except Exception as e:
                raise Exception(f"Error calling app {app_id}: {str(e)}")

    # ----------------------------------------------------------------------
    def manifest(self, app_id: str) -> dict:
        """
        Retrieves the manifest metadata for a specific application.

        Args:
            app_id (str): The application ID for which to retrieve the manifest.

        Returns:
            dict: The manifest data for the app, or an empty dictionary if not found.
        """
        return self._manifest.get(app_id, {})

    # ----------------------------------------------------------------------
    def schema(self, app_id: str, type: Literal['input', 'output']) -> dict:
        """
        Retrieves the input or output schema for a specific application.

        Args:
            app_id (str): The application ID for which to retrieve the schema.
            type (Literal['input', 'output']): The type of schema to retrieve.

        Returns:
            dict: The requested schema (input or output).

        Raises:
            ValueError: If the schema type is invalid or the schema is not found.
        """
        _input, _output = self._schema.get(app_id, (None, None))

        if type == 'input':
            if _input is None:
                raise ValueError(f"Input schema not found for app ID: {app_id}")
            return _input or {}
        elif type == 'output':
            if _output is None:
                raise ValueError(f"Output schema not found for app ID: {app_id}")
            return _output or {}
        else:
            raise ValueError("Type must be either 'input' or 'output'")

    def is_app_available(self, app_id: str) -> bool:
        """Check if an app is available."""
        return app_id in self.initialized_apps

    def get_available_apps(self) -> List[str]:
        """Get list of successfully initialized apps."""
        return list(self.initialized_apps)
