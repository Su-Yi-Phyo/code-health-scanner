from github import download_repository


repository_url = "https://github.com/octocat/Hello-World"

try:
    path = download_repository(repository_url)

    print("Download successful!")
    print("Repository extracted to:")
    print(path)

except Exception as error:
    print("Download failed!")
    print(error)