from typing import List

from fastapi import APIRouter, UploadFile, File
from pydantic import BaseModel
import os

from index import index_data, DATA_FOLDER, is_index, files_status, search_githubs
from retriever import naive_retrieval, reranked_retrieval

chat_router = router = APIRouter()


class ResumeQuery(BaseModel):
    job_description: str
    top_k: int = 5


@router.post('/upload')
def upload_files(files: List[UploadFile] = File(...)):
    upload_folder = DATA_FOLDER
    os.makedirs(upload_folder, exist_ok=True)

    file_details = []

    for file in files:
        file_location = f"{upload_folder}/{file.filename}"
        with open(file_location, "wb+") as file_object:
            file_object.write(file.file.read())
        file_details.append({"filename": file.filename, "location": file_location})

    return {"message": "Files uploaded successfully", "files": file_details}

@router.get('/files')
def get_files_status():
    indexed, not_indexed = files_status()
    return {
        "indexed": indexed,
        "not_indexed": not_indexed,
    }

@router.post('/index')
def index_files():
    index_data()
    return {"message": "Files indexed"}


@router.get('/index')
def index_exists():
    return {"exists": is_index()}


@router.post('/simple')
def return_naive_matches(resume_query: ResumeQuery):
    try:
        response = naive_retrieval(resume_query.job_description, resume_query.top_k)
        return {
            "hits": response
        }
    except Exception as e:
        return {
            "error": "You don't have any indexed files. Upload some and press the index button."
        }

@router.post('/reranked')
def return_reranked_matches(resume_query: ResumeQuery):
    try:
        response = reranked_retrieval(resume_query.job_description, resume_query.top_k)
        return {
            "hits": response
        }
    except:
        return {
            "error": "You don't have any indexed files. Upload some and press the index button."
        }

@router.get('/resumes')
def return_resume_analysis():
    users = search_githubs()
    return users