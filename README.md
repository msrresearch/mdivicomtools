# mdivicomtools

**mdivicomtools** is a Python-based package designed for building and running analysis pipelines, specifically tailored for research in multimodal visual communication. It is developed as part of the [mdinteract](https://vicom.info/projects/multimodal-assessment-of-dyadic-interaction-in-disorders-of-social-interaction) project within the DFG Priority Program Visual Communication ([ViCom](https://vicom.info)).

This repository provides core utilities along with modular components integrated via Git submodules, streamlining data processing and analysis workflows.

**Note:** The repository is under active development. Core functionalities are available, with additional features being progressively integrated.

---

## Quick Start Guide

### Installation for Users

1. **Clone the repository (with submodules):**

```bash
git clone --recurse-submodules https://github.com/yourname/mdivicomtools.git
```

If you initially cloned without submodules:

```bash
cd mdivicomtools
git submodule update --init --recursive
```

2. **Install dependencies:**

Use a Python virtual environment (recommended)

```bash
python -m venv venv
source venv/bin/activate  # on Windows: venv\Scripts\activate
```

Then install the main utilities and submodules:

```bash
# install optional submodules
pip install ./tools/mdipplcloud
pip install ./tools/mdimediaprep
pip install ./tools/mdifacetools
# install main utilities
pip install .
```

### Setup for Developers

To contribute or develop locally, install modules in editable mode:

```bash
# install optional submodules in editable mode
pip install -e ./tools/mdipplcloud
pip install -e ./tools/mdimediaprep
pip install -e ./tools/mdifacetools
# install main utilities in editable mode
pip install -e .
```

---

Below is a short snippet you could include in your **README** under a “Logging Setup” section:

---

### Logging Setup

**mdivicomtools** provides convenient logging setups. For quick usage, just call `setup_logging()`:

```python
from mdivicomtools.utils import setup_logging
setup_logging(preset="console_debug")
```

#### Available Presets
- **`console_debug`**  
  All messages at DEBUG level and above go to the console.
- **`console_info_file_debug`**  
  INFO-level messages go to the console, and DEBUG-level messages are saved to `mdivicomtools_debug.log`.
- **`json_console_debug`**  
  DEBUG-level messages to console, formatted as JSON (requires `python-json-logger`).

#### Advanced Usage
For custom logging setups, pass your own dictionary config:
```python
my_config = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": { ... },
    "root": { ... }
    # etc.
}
setup_logging(dict_config_override=my_config)
```
Or configure Python’s `logging` manually without calling `setup_logging()`.

## Working with Submodules

### Adding a New Submodule

To add a new submodule as a standalone Python package:

```bash
git submodule add <repository-url> tools/<new-module-name>
git commit -m "chore: add new submodule <new-module-name>"
git push origin main
```

### Updating Submodules

To update all submodules to their latest commits:

```bash
git submodule update --remote --recursive
git commit -am "chore: update all submodules"
git push origin main
```

To update a specific submodule branch:

```bash
cd tools/<submodule-name>
git checkout <branch-name>
git pull
cd ../..
git add tools/<submodule-name>
git commit -m "chore: update submodule <submodule-name> to latest <branch-name>"
git push origin main
```

---

## Example Usage

Here's a minimal example showing how to combine functionalities across modules:

```python

```

---

## Contributing

Contributions are welcome! Follow these steps:

1. Fork and clone your fork.
2. Create a feature branch (`git checkout -b feat/<new-feature>`).
3. Develop and test changes.
4. Push changes and open a Pull Request.

---

## Roadmap

- Expand module features
- Automated integration testing
- Publish to PyPI
- Setup Continuous Integration/Continuous Deployment (CI/CD) via GitHub Actions

---

## License

This repository is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

(c) 2025 Martin Schulte-Rüther and the mdinteract project team

---

## Support

For questions or issues, please open an issue or contact the maintainers directly.
