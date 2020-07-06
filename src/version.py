import git


def get_version():
    r = git.repo.Repo(search_parent_directories=True)
    return r.git.describe("--tags")


__VERSION__ = get_version()
