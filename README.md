# mdivicomtools

**mdivicomtools** is a Python-based package designed for building and running analysis pipelines, specifically tailored for research in multimodal visual communication. It is developed as part of the [mdinteract](https://vicom.info/projects/multimodal-assessment-of-dyadic-interaction-in-disorders-of-social-interaction) project within the DFG Priority Program Visual Communication ([ViCom](https://vicom.info)).

This repository provides the **public core**: a lightweight CLI + contracts that can discover and run **plugins** (separate Python packages or container tools). The goal is extensibility without forcing a shared dependency stack.

**Note:** The repository is under active development. In this early alpha version core functionality is available, with additional plugins and features being progressively integrated.

---

## Quick Start Guide

### Installation for Users

The default end-user story does **not** require git submodules. Install the core, then install plugins as needed.

Use a Python virtual environment (recommended):

```bash
# python venv
python -m venv .venv
source .venv/bin/activate  # on Windows: .venv\Scripts\activate
# conda
conda create -n mdivicomtools python=3.10
conda activate mdivicomtools  

```

Then install the core from GitHub (until we publish to PyPI):

```bash
pip install -U pip
pip install git+https://github.com/msrresearch/mdivicomtools.git
```

### Install plugins (optional)

Plugins are separate packages that register themselves via Python entry points (`mdivicomtools.plugins`). Install only what you need.

Example: optional Pupil Labs Cloud helper (installed as a separate package, not via submodule):

```bash
pip install git+https://github.com/msrresearch/mdipplcloud.git
```

### Install core + a plugin bundle (recommended for onboarding)

If you have a given list of plugins, the easiest onboarding is: install core + plugins in one go.

One command:

```bash
pip install \
  git+https://github.com/msrresearch/mdivicomtools.git \
  git+https://github.com/msrresearch/mdipplcloud.git
```

Repeatable installs via a requirements file (pin to commits/tags for reproducibility):

```text
# requirements-bundle.txt
git+https://github.com/msrresearch/mdivicomtools.git@main
git+https://github.com/msrresearch/mdipplcloud.git@main
```

```bash
pip install -r requirements-bundle.txt
```

Then:

```bash
mdivicom plugins list
mdivicom plugins info <plugin_id>
```

### Setup for Developers

To contribute or develop locally:

```bash
git clone https://github.com/msrresearch/mdivicomtools.git
cd mdivicomtools
pip install -e .
```

Optional (developer convenience only): initialize submodules if you want to hack on anything under `tools/` locally.

```bash
git submodule update --init --recursive
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
- Add more plugins (python + container)
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
