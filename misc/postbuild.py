import glob
import os

import git

r = git.repo.Repo()
v = r.git.describe("--tags")
for f in glob.glob("dist/*.exe"):
    fn = list(os.path.splitext(f))
    fn[0] += "-"
    fn[0] += v
    fn = "".join(fn)
    os.rename(f, fn)
