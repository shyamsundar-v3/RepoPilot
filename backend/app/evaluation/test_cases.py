TEST_CASES = [
    {
        "repo_url": "https://github.com/pallets/click",
        "question": "What is the main entry point of this project?",
        "expected_evidence_files": ["src/click/__init__.py", "src/click/core.py"],
        "section": "overview",
    },
    {
        "repo_url": "https://github.com/pallets/click",
        "question": "What are the main dependencies?",
        "expected_evidence_files": ["setup.cfg", "pyproject.toml", "requirements.txt"],
        "section": "dependencies",
    },
    {
        "repo_url": "https://github.com/pallets/click",
        "question": "How is the CLI argument parsing implemented?",
        "expected_evidence_files": ["src/click/core.py", "src/click/parser.py"],
        "section": "code_flow",
    },
]
