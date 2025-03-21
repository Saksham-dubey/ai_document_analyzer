from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
from workflows.jobs.pdf_processor import PDFProcessor
from workflows.utils.utils import list_pdf_files,delete_all_pdfs
app = FastAPI()
from workflows.utils.supabase import execute_query, generate_query
from sqlalchemy import create_engine
from workflows.jobs.fetch_and_store_pdf import fetch_and_download_pdfs
# Configure CORS
pdf_directory = os.path.join(os.getcwd(), "PDF_2")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Initialize PDF processor with your PDF files
pdf_processor = PDFProcessor(api_key=os.getenv('OPENAI_API_KEY'))




class QueryRequest(BaseModel):
    query: str

class CompanyValues(BaseModel):
    name: str


@app.get("/get_companies")
async def get_companies():
    pdf_processor.cleanup_files()
    delete_all_pdfs(pdf_directory)
    get_company_values = generate_query(type_query="get_distinct_values", column_name="name", schema="darvin_pro", table_name="entity",column_name_1="entity_type",value="Company")

    engine = create_engine(os.getenv("DATABASE_URL"))

    get_column_values = execute_query(engine, get_company_values)
    print(get_column_values)
    get_column_values = get_column_values["name"].tolist()
    print(get_column_values)
    return {"companies": get_column_values}

@app.post("/get_entity_name")
async def get_company_values(company_values: CompanyValues):
    try:
        fetch_and_download_pdfs(entity_name=company_values.name, pdf_directory=pdf_directory)
        PDF_PATHS = list_pdf_files(pdf_directory)
        
        if not PDF_PATHS:  # If no PDFs were found
            return {"status": "no_pdfs", "message": "No PDFs found for this company"}
            
        pdf_processor.upload_pdfs(PDF_PATHS)
        return {"status": "success", "message": "PDFs uploaded successfully"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("home.html", {"request": request})

@app.get("/chat", response_class=HTMLResponse)
async def chat(request: Request):
    return templates.TemplateResponse("chat.html", {"request": request})

@app.post("/process-query")
async def process_query(query_request: QueryRequest):
    if not query_request.query:
        raise HTTPException(status_code=400, detail="No query provided")
    
    try:
        response = pdf_processor.process_query(query_request.query)
        return {"response": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/cleanup")
async def cleanup():
    try:
        pdf_processor.cleanup_files()
        return {"message": "Cleanup successful"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    try:
        uvicorn.run(app, host="0.0.0.0", port=8000)
    finally:
        # Clean up files when the application shuts down
        pdf_processor.cleanup_files() 
