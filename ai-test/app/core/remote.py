from typing import Optional, Union

from openfabric_pysdk.helper import Proxy
from openfabric_pysdk.helper.proxy import ExecutionResult


class Remote:
    """
    Remote is a helper class that interfaces with an Openfabric Proxy instance
    to send input data, execute computations, and fetch results synchronously
    or asynchronously.

    Attributes:
        proxy_url (str): The URL to the proxy service.
        proxy_tag (Optional[str]): An optional tag to identify a specific proxy instance.
        client (Optional[Proxy]): The initialized proxy client instance.
    """

    # ----------------------------------------------------------------------
    def __init__(self, proxy_url: str, proxy_tag: Optional[str] = None):
        """
        Initializes the Remote instance with the proxy URL and optional tag.

        Args:
            proxy_url (str): The base URL of the proxy.
            proxy_tag (Optional[str]): An optional tag for the proxy instance.
        """
        self.proxy_url = proxy_url
        self.proxy_tag = proxy_tag
        self.client: Optional[Proxy] = None

    # ----------------------------------------------------------------------
    def connect(self) -> 'Remote':
        """
        Establishes a connection with the proxy by instantiating the Proxy client.

        Returns:
            Remote: The current instance for chaining.

        Raises:
            Exception: If the connection fails to establish.
        """
        try:
            self.client = Proxy(self.proxy_url, self.proxy_tag, ssl_verify=False)
            # Test the connection with a simple request
            test_result = self.client.request({"test": "connection"}, "test-connection")
            if test_result is None:
                raise Exception("Failed to establish WebSocket connection")
            return self
        except Exception as e:
            raise Exception(f"Failed to connect to {self.proxy_url}: {str(e)}")

    # ----------------------------------------------------------------------
    def execute(self, inputs: dict, uid: str) -> Union[ExecutionResult, None]:
        """
        Executes an asynchronous request using the proxy client.

        Args:
            inputs (dict): The input payload to send to the proxy.
            uid (str): A unique identifier for the request.

        Returns:
            Union[ExecutionResult, None]: The result of the execution, or None if not connected.

        Raises:
            Exception: If the client is not connected or the request fails.
        """
        if self.client is None:
            raise Exception("Not connected to proxy service")

        try:
            result = self.client.request(inputs, uid)
            if result is None:
                raise Exception("No response received from proxy service")
            return result
        except Exception as e:
            raise Exception(f"Failed to execute request: {str(e)}")

    # ----------------------------------------------------------------------
    @staticmethod
    def get_response(output: ExecutionResult) -> Union[dict, None]:
        """
        Waits for the result and processes the output.

        Args:
            output (ExecutionResult): The result returned from a proxy request.

        Returns:
            Union[dict, None]: The response data if successful, None otherwise.

        Raises:
            Exception: If the request failed or was cancelled.
        """
        if output is None:
            raise Exception("No output result provided")

        try:
            output.wait()
            status = str(output.status()).lower()
            if status == "completed":
                data = output.data()
                if data is None:
                    raise Exception("No data received in completed response")
                return data
            if status == "cancelled":
                raise Exception("The request was cancelled by the proxy service")
            if status == "failed":
                raise Exception("The request failed in the proxy service")
            raise Exception(f"Unknown status received: {status}")
        except Exception as e:
            raise Exception(f"Error processing response: {str(e)}")

    # ----------------------------------------------------------------------
    def execute_sync(self, inputs: dict, configs: dict, uid: str) -> Union[dict, None]:
        """
        Executes a synchronous request with configuration parameters.

        Args:
            inputs (dict): The input payload.
            configs (dict): Additional configuration parameters.
            uid (str): A unique identifier for the request.

        Returns:
            Union[dict, None]: The processed response, or None if not connected.

        Raises:
            Exception: If the client is not connected or the request fails.
        """
        if self.client is None:
            raise Exception("Not connected to proxy service")

        try:
            output = self.client.execute(inputs, configs, uid)
            return Remote.get_response(output)
        except Exception as e:
            raise Exception(f"Failed to execute synchronous request: {str(e)}")
