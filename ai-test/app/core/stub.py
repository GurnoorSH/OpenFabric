import json
import logging
import pprint
import time
from typing import Any, Dict, List, Literal, Tuple

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
        Initializes the Stub instance by loading manifests, schemas, and connections
        for each given app ID.

        Args:
            app_ids (List[str]): A list of application identifiers (hostnames or URLs).
            max_retries (int): Maximum number of retry attempts for failed requests.
            retry_delay (int): Delay in seconds between retry attempts.
            require_all_apps (bool): If True, raises an exception if any app fails to initialize.
        """
        self._schema: Schemas = {}
        self._manifest: Manifests = {}
        self._connections: Connections = {}
        self._initialized_apps: List[str] = []
        self._max_retries = max_retries
        self._retry_delay = retry_delay
        self._require_all_apps = require_all_apps

        # Configure retry strategy
        retry_strategy = Retry(
            total=max_retries,
            backoff_factor=1,
            status_forcelist=[500, 502, 503, 504]
        )
        self._session = requests.Session()
        self._session.mount("https://", HTTPAdapter(max_retries=retry_strategy))

        failed_apps = []
        for app_id in app_ids:
            base_url = app_id.strip('/')
            retry_count = 0

            while retry_count < max_retries:
                try:
                    # Fetch manifest with increased timeout and response validation
                    manifest_url = f"https://{base_url}/manifest"
                    logging.info(f"[{app_id}] Fetching manifest from: {manifest_url}")
                    manifest_response = self._session.get(manifest_url, timeout=30)
                    manifest_response.raise_for_status()
                    
                    if not manifest_response.text:
                        raise Exception("Empty response received from manifest endpoint")
                    
                    manifest = manifest_response.json()
                    logging.info(f"[{app_id}] Manifest loaded: {manifest}")
                    self._manifest[app_id] = manifest

                    # Fetch input schema with validation
                    input_schema_url = f"https://{base_url}/schema?type=input"
                    logging.info(f"[{app_id}] Fetching input schema from: {input_schema_url}")
                    input_schema_response = self._session.get(input_schema_url, timeout=30)
                    input_schema_response.raise_for_status()
                    
                    if not input_schema_response.text:
                        raise Exception("Empty response received from input schema endpoint")
                    
                    input_schema = input_schema_response.json()
                    logging.info(f"[{app_id}] Input schema loaded: {input_schema}")

                    # Fetch output schema with validation
                    output_schema_url = f"https://{base_url}/schema?type=output"
                    logging.info(f"[{app_id}] Fetching output schema from: {output_schema_url}")
                    output_schema_response = self._session.get(output_schema_url, timeout=30)
                    output_schema_response.raise_for_status()
                    
                    if not output_schema_response.text:
                        raise Exception("Empty response received from output schema endpoint")
                    
                    output_schema = output_schema_response.json()
                    logging.info(f"[{app_id}] Output schema loaded: {output_schema}")
                    self._schema[app_id] = (input_schema, output_schema)

                    # Establish Remote WebSocket connection
                    ws_url = f"wss://{base_url}/app"
                    logging.info(f"[{app_id}] Establishing WebSocket connection to: {ws_url}")
                    self._connections[app_id] = Remote(ws_url, f"{app_id}-proxy").connect()
                    logging.info(f"[{app_id}] Connection established.")
                    self._initialized_apps.append(app_id)
                    break  # Success, exit retry loop

                except requests.exceptions.RequestException as e:
                    retry_count += 1
                    if retry_count < max_retries:
                        logging.warning(f"[{app_id}] Attempt {retry_count} failed: {str(e)}. Retrying in {self._retry_delay} seconds...")
                        time.sleep(self._retry_delay)
                    else:
                        error_msg = f"Network error while connecting to {app_id} after {max_retries} attempts: {str(e)}"
                        logging.error(error_msg)
                        if self._require_all_apps:
                            raise Exception(error_msg)
                        else:
                            failed_apps.append(app_id)
                            logging.warning(f"App {app_id} failed to initialize, but continuing with available apps")
                except json.JSONDecodeError as e:
                    error_msg = f"Invalid JSON response from {app_id}: {str(e)}"
                    logging.error(error_msg)
                    if self._require_all_apps:
                        raise Exception(error_msg)
                    else:
                        failed_apps.append(app_id)
                        logging.warning(f"App {app_id} failed to initialize, but continuing with available apps")
                except Exception as e:
                    error_msg = f"Failed to initialize app {app_id}: {str(e)}"
                    logging.error(error_msg)
                    if self._require_all_apps:
                        raise Exception(error_msg)
                    else:
                        failed_apps.append(app_id)
                        logging.warning(f"App {app_id} failed to initialize, but continuing with available apps")

        if not self._initialized_apps:
            raise Exception("No apps were successfully initialized. Please check your app IDs and network connection.")
        
        if failed_apps:
            logging.warning(f"The following apps failed to initialize: {', '.join(failed_apps)}")
            logging.info(f"Successfully initialized apps: {', '.join(self._initialized_apps)}")

    # ----------------------------------------------------------------------
    def call(self, app_id: str, data: Any, uid: str = 'super-user') -> dict:
        """
        Sends a request to the specified app via its Remote connection.

        Args:
            app_id (str): The application ID to route the request to.
            data (Any): The input data to send to the app.
            uid (str): The unique user/session identifier for tracking (default: 'super-user').

        Returns:
            dict: The output data returned by the app.

        Raises:
            Exception: If no connection is found for the provided app ID, or execution fails.
        """
        if app_id not in self._initialized_apps:
            raise Exception(f"App {app_id} was not successfully initialized during startup")

        connection = self._connections.get(app_id)
        if not connection:
            raise Exception(f"Connection not found for app ID: {app_id}")

        try:
            handler = connection.execute(data, uid)
            result = connection.get_response(handler)

            if not result:
                raise Exception(f"No response received from app {app_id}")

            schema = self.schema(app_id, 'output')
            marshmallow = json_schema_to_marshmallow(schema)
            handle_resources = has_resource_fields(marshmallow())

            if handle_resources:
                result = resolve_resources("https://" + app_id + "/resource?reid={reid}", result, marshmallow())

            return result
        except Exception as e:
            logging.error(f"[{app_id}] Execution failed: {e}")
            raise Exception(f"Failed to execute app {app_id}: {str(e)}")

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
            return _input
        elif type == 'output':
            if _output is None:
                raise ValueError(f"Output schema not found for app ID: {app_id}")
            return _output
        else:
            raise ValueError("Type must be either 'input' or 'output'")

    def is_app_available(self, app_id: str) -> bool:
        """
        Check if a specific app is available and initialized.

        Args:
            app_id (str): The application ID to check.

        Returns:
            bool: True if the app is available, False otherwise.
        """
        return app_id in self._initialized_apps

    def get_available_apps(self) -> List[str]:
        """
        Get a list of all successfully initialized apps.

        Returns:
            List[str]: List of available app IDs.
        """
        return self._initialized_apps.copy()
