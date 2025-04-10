# mdivicomtools

> **Umbrella Repository** for modular, reusable components (submodules). Each submodule is self-contained and can be used independently or integrated into a broader workflow. The current submodules are:
> 1. **mdivicomutils** – General-purpose utilities (data handling, common helpers).
> 2. **mdimediaprep** – Tools for processing and analyzing media files.
> 3. **mdifacetools** – Specialized components for face-detection or face-related tasks.

---

## 1. Overview

**mdivicomtools** is a collection of Python submodules focusing on streamlined data/media processing and specialized face-detection tasks. While each submodule can run standalone, this umbrella repository brings them together for integrated usage.

**Submodules (Git Repos)**:
- [mdivicomutils](https://github.com/yourname/mdivicomutils.git)
- [mdimediaprep](https://github.com/yourname/mdimediaprep.git)
- [mdifacetools](https://github.com/yourname/mdifacetools.git)

> **Note**: In the future, “simple users” can install these tools more easily if you publish them to PyPI (e.g. `pip install mdivicomtools`). Currently, this repo is best for developers who want to work with the submodules directly.

---

## 2. Quick Start (Developers)

### 2.1. Clone This Repository with Submodules

```bash
git clone --recurse-submodules https://github.com/yourname/mdivicomtools.git

If you forget --recurse-submodules:

cd mdivicomtools
git submodule update --init --recursive

2.2. Install Submodules (Editable Mode)

Each submodule manages its own dependencies in a requirements.txt or pyproject.toml. For local development, you can install each submodule in “editable” mode so changes are immediately reflected.

# Example:
pip install -e ./mdivicomutils
pip install -e ./mdimediaprep
pip install -e ./mdifacetools

Tip: If you prefer to install all dependencies at once, you can create a top-level requirements.txt referencing each submodule’s file. This is optional; see “Experimental Joint Requirements” below.

⸻

3. Working with Submodules

3.1. Add a New Submodule

git submodule add <url-of-new-module> new-module-folder

Then commit the reference in the umbrella repository:

git add new-module-folder
git commit -m "chore: add new submodule <module name>"
git push origin main

3.2. Update Submodules

Pull changes from each submodule’s remote repository:

git submodule update --remote

If any submodule is on a specific branch, you can:

cd mdivicomutils
git checkout <branch>
git pull

Then update the pointer in the umbrella repo:

cd ..
git add mdivicomutils
git commit -m "chore: update submodule reference for mdivicomutils"
git push origin main

3.3. Committing Changes Inside a Submodule

When you edit a submodule:

cd mdivicomutils
# make changes, then:
git add .
git commit -m "feat: add new utility function"
git push origin <branch>

Afterward, return to the umbrella:

cd ..
git add mdivicomutils
git commit -m "chore: updated mdivicomutils reference in umbrella"
git push origin main



⸻

4. Handling Dependencies

4.1. Submodule-Specific Requirements

Each submodule has its own requirements.txt or pyproject.toml. Install them individually:

cd mdivicomutils
pip install -r requirements.txt
cd ../mdimediaprep
pip install -r requirements.txt
# ... and so on

4.2. (Optional) Experimental Joint Requirements

You can create a top-level requirements.txt:

# requirements.txt
-r mdivicomutils/requirements.txt
-r mdimediaprep/requirements.txt
-r mdifacetools/requirements.txt

Then:

pip install -r requirements.txt

This installs all dependencies in one go. Be mindful of potential version conflicts.

⸻

5. Example Usage

Below is a minimal example showing how you might integrate multiple submodules in Python:

# Example: combine functionalities

from mdivicomutils.placeholder import xyz
from mdimediaprep.placeholder import xyz
from mdifacetools.placeholder import xyz

# 1) Use a common data helper

# 2) Prepare a video for further analysis

# 3) Detect faces in the processed media



⸻

6. Contributing
	1.	Fork and Clone: Fork the main repo, then clone locally with submodules.
	2.	Create a Branch: git checkout -b feat/awesome-feature
	3.	Code and Test: Make changes, add tests in each submodule, run them (pytest, etc.).
	4.	Commit and Push: Commit changes in submodules, then update the umbrella pointer.
	5.	Pull Request: Open a PR to merge into main.

⸻

7. License

This work is licensed under the Creative Commons Attribution-NonCommercial 4.0 International License.
You may obtain a copy of the License at:
http://creativecommons.org/licenses/by-nc/4.0/


⸻

8. Roadmap
	1.	Refine Submodule Architectures – Possibly break out specialized modules if they grow large.
	2.	Automated Testing – Add top-level integration tests for cross-submodule workflows.
	3.	PyPI Publishing – Provide an easier “pip install mdivicomtools” in the future.
	4.	CI/CD – Automate building, testing, and release pipelines.

⸻

Questions or Issues?

Please open an issue in this repository or contact the maintainers directly.

⸻