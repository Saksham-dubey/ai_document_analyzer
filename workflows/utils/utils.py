import os
from workflows.logs.log import setup_logger
import json
import requests
from urllib.parse import urlparse

logging = setup_logger()

def list_pdf_files(pdf_directory):
    pdf_files_list = []  # List to store tuples of (filename, full_path)
    logging.info(f"Listing PDF files in {pdf_directory}")
    if not os.path.exists(pdf_directory):
        print(f"Directory '{pdf_directory}' does not exist!")
        return pdf_files_list
    
    try:
        # Walk through directory and all subdirectories
        for root, dirs, files in os.walk(pdf_directory):
            for file in files:
                if file.lower().endswith('.pdf'):
                    full_path = os.path.join(root, file)
                    pdf_files_list.append( full_path)
        logging.info(f"Found {len(pdf_files_list)} PDF files")
        return pdf_files_list
                
    except Exception as e:
        print(f"Error accessing directory: {e}")
        logging.error(f"Error accessing directory: {e}")
        return pdf_files_list

def download_pdfs_from_urls(pdf_urls_list, folder_directory):
    """
    Download PDFs from a list of URLs and store them in the PDF directory
    Args:
        pdf_urls_list (list): List of PDF URLs to download
        entity_name (str): Name of the entity folder to store PDFs
    Returns:
        list: List of paths where PDFs were saved
    """
    # Create PDF directory if it doesn't exist
    pdf_dir = folder_directory
    os.makedirs(pdf_dir, exist_ok=True)
    
    downloaded_files = []
    max_pdfs = min(6, len(pdf_urls_list))  # Limit to 6 PDFs
    
    # Headers to mimic a browser request
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Connection': 'keep-alive',
    }
    
    # Create a session to maintain cookies
    session = requests.Session()
    session.headers.update(headers)
    
    for url in pdf_urls_list[:max_pdfs]:
        try:
            # Skip None or empty URLs
            if not url or url.lower() == 'none':
                continue
                
            # Clean up malformed URLs
            url = url.strip()
            url = url.split('@')[-1] if '@' in url else url
            
            # Ensure URL starts with http:// or https://
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url
            
            # Get filename from URL or use a default name
            parsed_url = urlparse(url)
            filename = os.path.basename(parsed_url.path)
            if not filename.endswith('.pdf'):
                filename = f"document_{len(downloaded_files)}.pdf"
            
            # Ensure filename is valid
            filename = ''.join(c for c in filename if c.isalnum() or c in '._- ')
            file_path = os.path.join(pdf_dir, filename)
            
            # First try to get the page
            logging.info(f"Attempting to download: {url}")
            response = session.get(url, stream=True, timeout=30)
            response.raise_for_status()
            
            # Check if we got a PDF
            content_type = response.headers.get('content-type', '').lower()
            if 'pdf' not in content_type:
                logging.warning(f"Warning: Content-Type is {content_type} for {url}")
                if response.status_code == 200:
                    logging.warning("Received 200 OK but content is not PDF - might require authentication")
                continue
            
            # Save the PDF
            with open(file_path, 'wb') as file:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        file.write(chunk)
            
            # Verify file was created and has content
            if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
                downloaded_files.append(file_path)
                logging.info(f"Successfully downloaded: {filename}")
            else:
                logging.error(f"File was created but appears to be empty: {filename}")
                if os.path.exists(file_path):
                    os.remove(file_path)
                
        except requests.exceptions.HTTPError as e:
            logging.error(f"HTTP Error for {url}: {e}")
            if e.response.status_code == 403:
                logging.error("Access forbidden - might require authentication")
            continue
        except requests.exceptions.ConnectionError as e:
            logging.error(f"Connection Error for {url}: {e}")
            continue
        except requests.exceptions.Timeout as e:
            logging.error(f"Timeout Error for {url}: {e}")
            continue
        except requests.exceptions.RequestException as e:
            logging.error(f"Error downloading PDF from {url}: {e}")
            continue
        except Exception as e:
            logging.error(f"Unexpected error for {url}: {e}")
            continue
    
    if not downloaded_files:
        logging.warning("No PDFs were successfully downloaded!")
    else:
        logging.info(f"Successfully downloaded {len(downloaded_files)} PDFs")
    
    return downloaded_files

def delete_all_pdfs(folder_directory):
    """
    Delete all PDF files from the PDF directory in the current working directory
    Returns:
        tuple: (bool, str) - (Success status, Message with operation details)
    """
    pdf_dir = folder_directory
    
    if not os.path.exists(pdf_dir):
        message = f"PDF directory does not exist at {pdf_dir}"
        logging.info(message)
        return False, message
    
    try:
        deleted_count = 0
        for root, dirs, files in os.walk(pdf_dir):
            for file in files:
                if file.lower().endswith('.pdf'):
                    file_path = os.path.join(root, file)
                    try:
                        os.remove(file_path)
                        deleted_count += 1
                        logging.info(f"Deleted: {file_path}")
                    except Exception as e:
                        logging.error(f"Failed to delete {file_path}: {str(e)}")
        
        # Optionally remove the PDF directory if it's empty
        if not os.listdir(pdf_dir):
            os.rmdir(pdf_dir)
            message = f"Deleted {deleted_count} PDF files and removed empty PDF directory"
        else:
            message = f"Deleted {deleted_count} PDF files, directory contains other files"
        
        logging.info(message)
        return True, message
        
    except Exception as e:
        message = f"Error while deleting PDFs: {str(e)}"
        logging.error(message)
        return False, message




    