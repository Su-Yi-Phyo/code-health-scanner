from github import download_repository
from scanner import find_python_files


repository_url = "https://github.com/octocat/Hello-World"

try:
    repository_path = download_repository(repository_url)

    python_files = find_python_files(repository_path)

    print(f"Found {len(python_files)} Python files:")

    for file in python_files:
        print(file)

except Exception as error:
    print("Scanner failed!")
    print(error)