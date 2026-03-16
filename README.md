# MASEO: A Multi-Agent System for Explainable Ontology Generation
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.19052004.svg)](https://doi.org/10.5281/zenodo.19052004)

This repository provides the artifact for ``MASEO``, a research-oriented multi-agent system that automated generate ontologies from competency questions, with a built-in focus on explainability. It aims to make the process of ontology generation more transparent, modular, and intelligent by distributing tasks among specialized agents. Each specialized agent is designed to keep track the logic behind each entity in generated ontology. 

## Project Structure

```bash

masoe/
├── dataset/          # Contains competency questions, generated & gold standard ontologies, run-time log
├── src/              # The core source code for the multi-agent system.
│   └── ...           # (Includes agent implementations, evaluation code)
└── README.md         # This file.

```

## Getting Started

1. **Clone the repository**
   ```bash
   git clone https://github.com/oeg-upm/masoe.git
   cd masoe
   ```

2. **Execute maseo system**
   ```
   Check the src/ directory for entry scripts and usage examples.
   ```
## Citation

If you use this framework in your research, please cite:

```bibtex
@inproceedings{xxx,
  title     = {MASEO: Multi Agent Systen for Explainable Ontology Generation},
  author    = {XXX},
  booktitle = {XXX},
  year      = {2026}
}
```

