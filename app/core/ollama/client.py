import os
import json
import logging
import requests
from typing import Dict, Any, List, Optional, Union

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OllamaClient:
    """Client for interacting with the Ollama API"""
    
    def __init__(self, base_url: str = "http://localhost:11434"):
        """
        Initialize the Ollama client
        
        Args:
            base_url: Base URL for the Ollama API
        """
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        
        # Test connection
        try:
            self.test_connection()
            logger.info(f"Successfully connected to Ollama API at {self.base_url}")
        except Exception as e:
            logger.error(f"Failed to connect to Ollama API: {str(e)}")
    
    def test_connection(self) -> bool:
        """Test connection to Ollama API"""
        try:
            response = requests.get(f"{self.api_url}/tags")
            response.raise_for_status()
            return True
        except Exception as e:
            logger.error(f"Connection test failed: {str(e)}")
            raise ConnectionError(f"Could not connect to Ollama API at {self.base_url}: {str(e)}")
    
    def list_models(self) -> List[Dict[str, Any]]:
        """List available models"""
        try:
            response = requests.get(f"{self.api_url}/tags")
            response.raise_for_status()
            return response.json().get("models", [])
        except Exception as e:
            logger.error(f"Failed to list models: {str(e)}")
            return []
    
    def generate(self, 
                 prompt: str, 
                 model: str = "deepseek-r1:1.5b", 
                 system: Optional[str] = None,
                 temperature: float = 0.7,
                 max_tokens: int = 2048) -> Dict[str, Any]:
        """
        Generate text using the specified model
        
        Args:
            prompt: The prompt to send to the model
            model: The model to use
            system: System prompt to use
            temperature: Sampling temperature (higher = more creative, lower = more deterministic)
            max_tokens: Maximum number of tokens to generate
            
        Returns:
            Dictionary containing the response
        """
        try:
            payload = {
                "model": model,
                "prompt": prompt,
                "temperature": temperature,
                "max_tokens": max_tokens,
                "stream": False
            }
            
            if system:
                payload["system"] = system
            
            response = requests.post(f"{self.api_url}/generate", json=payload)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to generate text: {str(e)}")
            return {"error": str(e)}
    
    def process_multiple_files(self, 
                              file_contents: List[Dict[str, str]], 
                              task_description: str,
                              model: str = "deepseek-r1:1.5b") -> Dict[str, Any]:
        """
        Process multiple files with a single prompt
        
        Args:
            file_contents: List of dictionaries with file_name and content keys
            task_description: Description of the task to perform on the files
            model: The model to use
            
        Returns:
            Dictionary containing the processed result
        """
        try:
            # Construct a prompt that includes all file contents
            files_text = ""
            for i, file_info in enumerate(file_contents):
                file_name = file_info.get("file_name", f"file_{i}")
                content = file_info.get("content", "")
                files_text += f"\n\n--- FILE: {file_name} ---\n{content}\n"
            
            # Create the full prompt
            prompt = f"""
            {task_description}
            
            Here are the files to process:
            {files_text}
            
            Please analyze these files and provide a comprehensive response.
            """
            
            # Use the generate method to process the files
            result = self.generate(
                prompt=prompt,
                model=model,
                system="You are an AI assistant specialized in analyzing educational content. Your task is to process multiple files and provide a comprehensive analysis.",
                temperature=0.3,  # Lower temperature for more focused results
                max_tokens=4096   # Increase token limit for longer responses
            )
            
            return {
                "status": "success",
                "result": result.get("response", ""),
                "files_processed": len(file_contents)
            }
        except Exception as e:
            logger.error(f"Failed to process multiple files: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "files_processed": 0
            }

# Create a singleton instance
ollama_client = OllamaClient()
