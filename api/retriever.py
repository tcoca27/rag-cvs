import logging

from index import get_index
import time
from ragatouille import RAGPretrainedModel

RAG = RAGPretrainedModel.from_pretrained("colbert-ir/colbertv2.0")

logger = logging.getLogger("uvicorn")


def naive_retrieval(job_description, top_k):
    start_time = time.process_time()
    retriever = get_index(top_k)
    documents = retriever.retrieve(job_description)
    logger.info(f"retrieved in {time.process_time() - start_time}")
    return list(
        map(lambda doc: {"file_name": doc.node.metadata['file_name'], "content": doc.node.get_content()}, documents))


def reranked_retrieval(job_description, top_k):
    documents = naive_retrieval(job_description, top_k*2)
    documents_content = list(map(lambda doc: doc['content'], documents))
    start_time = time.process_time()
    reranked = RAG.rerank(query=job_description, documents=documents_content, k=top_k)
    logger.info(f"reranked in {time.process_time() - start_time}")
    result = []
    for initial_doc in documents:
        for reranked_doc in reranked:
            if initial_doc['content'] == reranked_doc['content']:
                result.append(initial_doc)
                continue
    return result
