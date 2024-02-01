import json
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
import re

from github_utils import get_personal_repos, get_repo_description, get_gpt_analysis

service_context = ServiceContext.from_defaults(chunk_size=1024, embed_model="local:BAAI/bge-small-en-v1.5", llm=None)

DATA_FOLDER = './data2'
PERSIST_DIR = './storage_small'
PERSIST_GIT = './storage_git/users.json'

is_index_ready = os.path.exists(PERSIST_DIR) and len(os.listdir(PERSIST_DIR)) > 0

logger = logging.getLogger("uvicorn")


def files_status():
    file_names = []
    if os.path.exists(DATA_FOLDER) and len(os.listdir(DATA_FOLDER)) > 0:
        file_names = os.listdir(DATA_FOLDER)
    file_names.remove('.DS_Store')
    to_index = []
    if is_index():
        storage_context = StorageContext.from_defaults(persist_dir=PERSIST_DIR)
        index = load_index_from_storage(storage_context, service_context=service_context)
        for file in file_names:
            path = os.path.join(DATA_FOLDER, file)
            if index.docstore.get_ref_doc_info(path[path.index('/') + 1:]) == None and index.docstore.get_ref_doc_info(path[path.index('/') + 1:] + '_part_0') == None:
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


def save_json(dictionary):
    json_object = json.dumps(dictionary, indent=4)

# Writing to sample.json
    with open(PERSIST_GIT, "w") as outfile:
        outfile.write(json_object)


def get_prev_user(prev_users, username):
    for user in prev_users:
        if user['username'] == username:
            return user

def search_githubs():
    prev_users = None
    try:
        with open(PERSIST_GIT) as user_file:
            prev_users = json.load(user_file)
    except:
        pass
    documents = SimpleDirectoryReader(DATA_FOLDER, filename_as_id=True).load_data()
    prev_usernames = map(lambda user: user['username'], prev_users) if prev_users is not None else []
    users = []
    current_usernames = []
    for doc in documents:
        text = doc.get_text()
        match = re.search(r'github\.com/([^/\s]+)', text)
        if match:
            username = match.group(1)
            current_usernames.append(username)
            if username in prev_usernames:
                users.append(get_prev_user(prev_users, username))
            else:
                users.append(get_user_object(username))
    if prev_users is not None and len(prev_users) > 0:
        for user in prev_users:
            if user['username'] not in current_usernames:
                users.append(user)
    save_json(users)
    return users


def get_user_object(username):
    personal_repos = get_personal_repos(username)
    print(f'Username: {username} Personal Repos: {personal_repos}')
    if len(personal_repos):
        descriptions = []
        for pr in personal_repos:
            description = get_repo_description(username, pr)
            if 'not analyzed' in description.lower():
                print(f'Repo could not be analyzed: {pr}')
                continue
            descriptions.append(get_repo_description(username, pr))
            print(f'Analyzed repo {pr}')
        full_analysis = get_gpt_analysis(descriptions.__str__())
        return {
            'username': username,
            'descriptions': descriptions,
            'analysis': full_analysis,
            'file_name': None
        }
    

def get_index(top_k=3):
    if not os.path.exists(PERSIST_DIR) or len(os.listdir(PERSIST_DIR)) == 0:
        raise Exception("Index does not exist")
    else:
        storage_context = StorageContext.from_defaults(persist_dir=PERSIST_DIR)
        index = load_index_from_storage(storage_context, service_context=service_context)
        return index.as_retriever(similarity_top_k=top_k)


def is_index():
    return is_index_ready