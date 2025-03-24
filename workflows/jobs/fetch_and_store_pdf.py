from workflows.utils.supabase import generate_query, execute_query
from workflows.utils.utils import download_pdfs_from_urls
from sqlalchemy import create_engine
import os

def fetch_and_download_pdfs(entity_name: str, pdf_directory: str = None) -> None:
    """
    Fetches PDF URLs for a given entity and downloads the PDFs to specified directory.
    
    Args:
        entity_name (str): Name of the entity to search for
        pdf_directory (str, optional): Directory to save PDFs. Defaults to 'PDF_2' in current working directory.
    """
    # Create database engine
    engine = create_engine(os.getenv("DATABASE_URL"))
    
    # Generate and execute query to get PDF URLs
    join_query = generate_query(
        type_query="join_table_left",
        schema="darvin_pro",
        table_1="entity",
        table_2="publications_feed",
        join_column="entity_id",
        column_name="name",
        value=entity_name
    )
    
    # Process the data
    get_joined_data = execute_query(engine, join_query)
    get_joined_data = get_joined_data[["entity_id", "name", "pdf_url"]]
    get_joined_data = get_joined_data.replace("None", None)
    get_joined_data = get_joined_data.dropna(subset=["pdf_url"])
    
    # Extract URLs and set up directory
    url_list = get_joined_data["pdf_url"].tolist()
    if pdf_directory is None:
        pdf_directory = os.path.join(os.getcwd(), "PDF_2")
    
    # Download PDFs
    download_pdfs_from_urls(pdf_urls_list=url_list, folder_directory=pdf_directory)

# if __name__ == "__main__":
#     # Example usage
#     fetch_and_download_pdfs("Dxcover")

