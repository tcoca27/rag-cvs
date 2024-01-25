import logging
from shutil import rmtree

from llama_index import (
    VectorStoreIndex,
    SimpleDirectoryReader,
    StorageContext,
    load_index_from_storage,
    ServiceContext
)
import os
import time

service_context = ServiceContext.from_defaults(chunk_size=1024, embed_model="local:BAAI/bge-small-en-v1.5", llm=None)

DATA_FOLDER = './uploaded_data'
PERSIST_DIR = './storage_small'

is_index_ready = os.path.exists(PERSIST_DIR) and len(os.listdir(PERSIST_DIR)) > 0

logger = logging.getLogger("uvicorn")


def files_status():
    file_names = []
    if os.path.exists(DATA_FOLDER) and len(os.listdir(DATA_FOLDER)) > 0:
        file_names = os.listdir(DATA_FOLDER)
    to_index = []
    if is_index():
        storage_context = StorageContext.from_defaults(persist_dir=PERSIST_DIR)
        index = load_index_from_storage(storage_context, service_context=service_context)
        for file in file_names:
            path = os.path.join(DATA_FOLDER, file)
            if index.docstore.get_ref_doc_info(path[path.index('/') + 1:]) == None:
                to_index.append(file)
    file_names = list(filter(lambda file: file not in to_index, file_names))
    return file_names, to_index


def index_data():
    start_load = time.process_time()
    documents = SimpleDirectoryReader(DATA_FOLDER, filename_as_id=True).load_data()
    logger.info(f'documents loaded in {time.process_time() - start_load}')
    global is_index_ready
    is_index_ready = False
    if os.path.exists(PERSIST_DIR) and len(os.listdir(PERSIST_DIR)) > 0:
        # for some reason index.insert does not index the new documents properly
        rmtree(PERSIST_DIR)
    start = time.process_time()
    index = VectorStoreIndex.from_documents(documents, service_context=service_context)
    index.storage_context.persist(persist_dir=PERSIST_DIR)
    logger.info(f'index created in {time.process_time() - start}')
    is_index_ready = True


def get_index(top_k=3):
    if not os.path.exists(PERSIST_DIR) or len(os.listdir(PERSIST_DIR)) == 0:
        raise Exception("Index does not exist")
    else:
        storage_context = StorageContext.from_defaults(persist_dir=PERSIST_DIR)
        index = load_index_from_storage(storage_context, service_context=service_context)
        return index.as_retriever(similarity_top_k=top_k)


def is_index():
    return is_index_ready