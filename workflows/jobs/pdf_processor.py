from openai import OpenAI
from typing import List, Dict, Any
from workflows.logs.log import setup_logger

class PDFProcessor:
    def __init__(self, api_key: str):
        """Initialize the PDFProcessor with OpenAI API key."""
        self.client = OpenAI(api_key=api_key)
        self.file_ids = []
        # Setup logger
        self.logger = setup_logger()
        self.logger.info("Initialized PDFProcessor")

    def upload_pdfs(self, pdf_paths: List[str]) -> None:
        """Upload PDFs to OpenAI and store their file IDs."""
        try:
            self.logger.info(f"Starting upload of {len(pdf_paths)} PDFs")
            for pdf_path in pdf_paths:
                with open(pdf_path, "rb") as file:
                    self.logger.debug(f"Uploading file: {pdf_path}")
                    uploaded_file = self.client.files.create(
                        file=file,
                        purpose="assistants"
                    )
                    self.file_ids.append(uploaded_file.id)
                    self.logger.debug(f"Successfully uploaded file {pdf_path} with ID: {uploaded_file.id}")
        except Exception as e:
            self.logger.error(f"Error uploading PDFs: {str(e)}")
            raise

    def process_query(self, query_text: str) -> str:
        """Process the query with uploaded PDFs and return response."""
        try:
            self.logger.info(f"Processing query: {query_text}")
            if not self.file_ids:
                self.logger.warning("No files uploaded before processing query")
                raise ValueError("No files have been uploaded")

            # Create content list with file IDs
            content_list = [
                {"type": "input_file", "file_id": file_id} 
                for file_id in self.file_ids
            ]
            
            # Append the query text
            content_list.append({
                "type": "input_text",
                "text": query_text
            })

            # Make API request
            self.logger.debug("Sending request to OpenAI API")
            response = self.client.responses.create(
                model="gpt-4o",
                input=[{
                    "role": "user",
                    "content": content_list
                }]
            )

            response_text = response.output[0].content[0].text
            self.logger.info("Successfully processed query")
            return response_text

        except Exception as e:
            self.logger.error(f"Error processing query: {str(e)}")
            raise

    def cleanup_files(self) -> None:
        """Delete all uploaded files."""
        try:
            self.logger.info("Starting cleanup of files")
            # Get list of all files
            files = self.client.files.list()
            files_list = [file.id for file in files.data]
            
            # Delete each file
            for file_id in files_list:
                self.logger.debug(f"Deleting file ID: {file_id}")
                self.client.files.delete(file_id)
            
            # Clear the stored file IDs
            self.file_ids = []
            self.logger.info(f"Successfully cleaned up {len(files_list)} files")

        except Exception as e:
            self.logger.error(f"Error cleaning up files: {str(e)}")
            raise

    async def process_pdfs_with_query(self, pdf_paths: List[str], query_text: str) -> str:
        """
        Convenience method to handle complete workflow with proper cleanup.
        Now with async support and context management.
        """
        self.logger.info("Starting complete PDF processing workflow")
        try:
            self.upload_pdfs(pdf_paths)
            response = self.process_query(query_text)
            return response
        except Exception as e:
            self.logger.error(f"Error in PDF processing workflow: {str(e)}")
            raise
        finally:
            self.logger.info("Cleaning up files regardless of success/failure")
            self.cleanup_files() 