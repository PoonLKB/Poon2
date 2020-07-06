import os

import git

r = git.repo.Repo()
with open(os.path.join("src", "version.py"), "w") as f:
    f.write("__VERSION__ = '%s'\n" % (r.git.describe("--tags")))
