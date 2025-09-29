# mdivicomtools

**mdivicomtools** is a Python-based package designed for building and running analysis pipelines, specifically tailored for research in multimodal visual communication. It is developed as part of the [mdinteract](https://vicom.info/projects/multimodal-assessment-of-dyadic-interaction-in-disorders-of-social-interaction) project within the DFG Priority Program Visual Communication ([ViCom](https://vicom.info)).

This repository provides core utilities and modular components (integrated via Git submodules). The package is designed to be extensible, allowing users to add their own modules or integrate existing ones.

**Note:** The repository is under active development. In this early alpha version core functionalities and selected submodules are available, with additional features being progressively integrated.

---

## Quick Start Guide

### Installation for Users

1. **Clone the repository (with submodules):**

```bash
git clone --recurse-submodules https://github.com/msrresearch/mdivicomtools.git
```

If you initially cloned without submodules:

```bash
cd mdivicomtools
git submodule update --init --recursive
```

2. **Install dependencies:**

Use a Python virtual environment (recommended)

```bash
# python venv
python -m venv venv
source venv/bin/activate  # on Windows: venv\Scripts\activate
# conda
conda create -n mdivicomtools python=3.10
conda activate mdivicomtools  

```

Then install the main utilities and submodules:

```bash
# install optional submodules
pip install ./tools/mdipplcloud
# install main utilities
pip install .
```

### Setup for Developers

To contribute or develop locally, install modules in editable mode:

```bash
# install optional submodules in editable mode
pip install -e ./tools/mdipplcloud
# install main utilities in editable mode
pip install -e .
```

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

## Contributing

Contributions are welcome! Follow these steps:

1. Fork and clone your fork.
2. Create a feature branch (`git checkout -b feat/<new-feature>`).
3. Develop and test changes.
4. Push changes and open a Pull Request.

---

## Roadmap

- Expand core module features
- Add more submodules
- Automated integration testing
- Publish to PyPI

---

## Citation
If you use this code in your research, please cite
- www.github.com/msrresearch/mdivicomtools

---

## License

This repository is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

(c) 2025 Martin Schulte-Rüther and the mdinteract project team

---

## Acknowledgements
This project was supported by the following grants to Martin Schulte-Rüther
DFG SCHU-2493/5-1 (Deutsche Forschungsgemeinschaft), LSC-AF2023_04 and LSC-AF2021_05 (Leibniz ScienceCampus).

## Contact
Martin Schulte-Rüther

Department of Child and Adolescent Psychiatry and Psychotherapy, University Hospital Heidelberg, Ruprechts-Karls-University Heidelberg, [martin.schulte-ruether@uni-heidelberg.de](mailto:martin.schulte-ruether@uni-heidelberg.de)

Department of Child and Adolescent Psychiatry and Psychotherapy, University Medical Center Göttingen, martin.schulte-ruether@med.uni-goettingen.de


For questions or issues, please open an issue or contact the maintainers directly.
