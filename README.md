# eightify

Relax and find insights.

## Usage

- Install in venv
  `python -m venv .venv && source .venv/bin/activate && pip install -r requirements.lock`
- Put creds in `.env`

## Development

- Install rye — yet another package manager, but from the creators of ruff:
  `curl -sSf https://rye.astral.sh/get | bash`
- Install env `rye sync`
- Install pre-commit hooks: `pre-commit install`
- Put creds in `.env`
- Run tests: `rye run pytest`
- Test from swagger docs: `127.0.0.1:8000/docs`

## TODO:

- Migrate to LLM framework (LangChain/HayStack)
- Automatic evaluation pipeline using LLM framework (too much to implement
  myself)
- Performance benchmarks
- Caching generated summaries and transcripts
- Divide backend and frontend into distinct packages
  - Retrieve relevant YouTube data for the frontend without directly using the
    internal backend code
- Fetch more comments, not only "relevant" ones for more insightful analysis
  - Maybe need to use https://github.com/egbertbouman/youtube-comment-downloader
