import os
from typing import List

from github import Github, Repository, PaginatedList

from github import Auth
from dotenv import load_dotenv
from openai import OpenAI
import ast
from llama_hub.github_repo import GithubClient, GithubRepositoryReader
from llama_index import download_loader

GPT_3 = "gpt-3.5-turbo-1106"

download_loader("GithubRepositoryReader")

load_dotenv()
auth = Auth.Token(os.getenv('GITHUB_API_KEY'))
g = Github(auth=auth)
client = OpenAI(
    api_key=os.getenv('OPENAI_API_KEY'),
)

SYSTEM_INSTRUCTION_PR = '''
You are senior developer with very high standards, specialized in analyzing GitHub repositories to identify potential internship candidates for our company. We value students who show creativity and a proactive mindset in working on personal projects, beyond just fulfilling university coursework. Your task is to review GitHub profiles and identify projects that reflect a student’s genuine interest and passion in coding.

To accomplish this, you will:

Examine each project's metadata, including the project name, description, programming language, and size.
Determine if a project is likely a personal initiative or just a university assignment. Personal projects often have unique names, detailed descriptions, use a variety of languages, and are of varying sizes. University projects tend to have generic names, lack detailed descriptions, or include the university related names like 'uni', 'ubb', 'university' etc.
Use the following criteria to assess the projects:

Project Name: Look for creativity and uniqueness.
Description: Evaluate the level of detail and whether it goes beyond basic assignment requirements. Usually a blank description means it's a course project, unless it has a very unique name, then it may be personal.
Size: the size of the project in lines of code
If you are not exactly sure if a project is personal or part of course work, don't classify it as personal. Be critical.
Your output will be a Python list of project titles that you consider to be personal projects, not university assignments. Here's an example of the type of metadata you might encounter:

Project Name: "EcoTracker"
Description: "An app for tracking and reducing personal carbon footprint, integrating real-time data and gamification elements."
Size: 30000

Project Name: "license"
Description: "Working on my bachelor thesis"
Size: 50000

Project Name: "UBB"
Description: ""
Size: 10000

Project Name: "AutOffside"
Description: "A system for automatic detection of offsides in football games"
Size: 70000

Based on your analysis, create a ONLY list of project titles that reflect personal initiatives. Don't output anything else! For the previous example:

personal_projects = ['EcoTracker', 'AutOffside']
'''

SYSTEM_INSTRUCTION_SUMM = '''
You are a well-rounded very skilled and demanding senior developer tasked with going over internship applications. 
Your task is to look over github projects and summarize them. 
In your summary you have to mention the name of the project and the username of the candidate, the programming language which was used,
describe the project as a whole, what it does and how it does it and also rate the skill and proficiency of the author.
Be very critical and tough in your analysis, not every project is necessarily a good one!
Students will be in the second or third year of their studies, but we're interested in only the more extraordinary ones.

Rate the following categories out of 5:
Proficiency in the programming language
Code cleanliness and readability
Code maintainability
Code quality and best practices
Innovation and creativity

If you can not analyze the project for whatever reason, write the following: 'Not analyzed'.
'''

SYSTEM_INSTRUCTION_FULL_SUMM = '''
You are well-rounded very skilled and demanding senior developer specialized in analyzing GitHub repositories to identify potential internship candidates for our company.
We value students who show creativity and a proactive mindset in working on personal projects, beyond just fulfilling university coursework, they must also be technical savy, showing very good techinical abilities. Your task is to review GitHub profiles and identify projects that reflect a student’s genuine interest and passion in coding.

You will receive the summary of their personal projects and you should do an overall evaluation of the student based
on what we value. Be critical and tough in your analysis, not every student is a good one!
students will be in the second or third year of their studies, but we're interested in only the more extraordinary ones.
'''


def create_prompt(repos: PaginatedList) -> str:
    result_prompt = ''
    for r in repos:
        if not r.fork:
            result_prompt += f'Project Name: "{r.name}" \nDescription: "{r.description}" \nSize: {r.size} \n'
    return result_prompt


def get_personal_repos_gpt_response(prompt: str) -> str:
    response = client.chat.completions.create(
        model=GPT_3,
        temperature=0,
        messages=[
            {
                "role": "system",
                "content": SYSTEM_INSTRUCTION_PR
            },
            {
                "role": "user",
                "content": prompt
            }
        ]
    )
    return response.choices[0].message.content


def get_gpt_repo_description(prompt: str) -> str:
    response = client.chat.completions.create(
        model="gpt-3.5-turbo-1106",
        temperature=0,
        messages=[
            {
                "role": "system",
                "content": SYSTEM_INSTRUCTION_SUMM
            },
            {
                "role": "user",
                "content": prompt
            }
        ]
    )
    return response.choices[0].message.content


def get_gpt_analysis(prompt: str) -> str:
    response = client.chat.completions.create(
        model="gpt-3.5-turbo-1106",
        temperature=0,
        messages=[
            {
                "role": "system",
                "content": SYSTEM_INSTRUCTION_FULL_SUMM
            },
            {
                "role": "user",
                "content": prompt
            }
        ]
    )
    return response.choices[0].message.content


def get_personal_repos(username: str) -> List[str]:
    user = g.get_user(username)
    repos = user.get_repos()
    response = None
    if repos.totalCount > 0:
        prompt = create_prompt(repos)
        retries = 3
        while not type(response) is list or retries > 0:
            try:
                llm_response = get_personal_repos_gpt_response(prompt)
                response = ast.literal_eval(llm_response.split('=')[1].strip())
                retries -= 1
            except:
                retries -= 1
    return response if type(response) is list else []


def keep_first_90_percent(dictionary):
    num_to_keep = int(len(dictionary) * 0.9)
    new_dict = {}
    for index, (key, value) in enumerate(dictionary.items()):
        if index < num_to_keep:
            new_dict[key] = value
        else:
            break

    return new_dict


def get_repo_description(username: str, repo_name: str) -> str:
    github_personal_key = os.getenv('GITHUB_API_KEY')
    repository_owner = username
    repository_name = repo_name
    file_extensions_to_include = [".py", ".ts", ".tsx", ".java", ".js", ".php", ".c", ".cpp", ".cs", ".html", ".css",
                                  ".scss", ".h", ".rb", ".swift", ".kt", ".kts", ".rs", ".sql", ".go", ".dart",
                                  ".pl", ".pm", ".scala"]
    github_branch = g.get_repo(f'{username}/{repo_name}').default_branch

    github_client = GithubClient(github_personal_key)
    loader = GithubRepositoryReader(
        github_client,
        owner=repository_owner,
        repo=repository_name,
        filter_file_extensions=(file_extensions_to_include, GithubRepositoryReader.FilterType.INCLUDE),
        concurrent_requests=10,
    )
    docs = loader.load_data(branch=github_branch)
    files = {}
    for d in docs:
        files[d.metadata['file_path']] = d.get_text()

    response = None
    while type(response) is not str:
        try:
            response = get_gpt_repo_description(f'Username: {username}\n Repository name: {repo_name}\n' + str(files))
        except:
            files = keep_first_90_percent(files)

    return response if type(response) is str else ''
