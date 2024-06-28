# Eightify

- ⏱️ Save time on long videos, get key ideas instantly
- 📚 Eightify helps when you're swamped with too much content
- 🧠 It's an AI YouTube tool which finds the key points in topics like AI,
  Business, Finance, News, or Health
- 🚀 Eightify boosts your learning
- 🔍 Navigate through videos with ease using summarized paragraphs with
  timestamps
- 💡 Get the pivotal points and key ideas from the video
- 🎯 Grasp the gist of any video in seconds with our YouTube summary AI
- 🌍 Access translations of summaries in your preferred language. No more
  language barriers with Eightify!

![put your video in the form](./img/main_page_1.png)
![get the video summary](./img/main_page_2.png)
![get insights from comments](./img/main_page_3.png)

## Usage

- Install in venv
  `python -m venv .venv && source .venv/bin/activate && pip install -r requirements.lock`
- Put creds in `.env`
- Start the backend in one terminal: `python src/eightify/main.py`
- Start the frontend in another terminal: `streamlit run src/eightify/app.py`
- Enjoy your time in the browser interface

## Development

- Install rye — yet another package manager, but from the creators of ruff:
  `curl -sSf https://rye.astral.sh/get | bash`
- Install env `rye sync`
- Install pre-commit hooks: `pre-commit install`
- Put creds in `.env`
- Run tests: `rye run pytest`
- Test backend from swagger docs: `127.0.0.1:8000/docs`

## Project structure

- `main.py` — backend FastAPI app
- `app.py` — fronted on Streamlit
- `api/youtube.py` — API calls to YouTube (descriptions, transcripts, comments)
- `api/llm.py` — LLM calls for transcript and comment summarization
- `config.py` — configuration with `pydantic-settings`

## TODO:

- Migrate to LLM framework (LangChain/HayStack)
- Automatic evaluation pipeline using LLM framework (too much to implement
  myself)
- Performance benchmarks
- Test on long videos (hope my LLM costs will be cheap enough)
- Caching generated summaries and transcripts
  - Database integration
  - Version the prompts used and the version of the app
  - Implement cache invalidation strategy — when the prompt changes
    (significantly?), generate anew
- Divide backend and frontend into distinct packages
  - Retrieve relevant YouTube data for the frontend without directly using the
    internal backend code
- Fetch more comments, not only "relevant" ones for more insightful analysis
  - May be relevant https://github.com/egbertbouman/youtube-comment-downloader
- Introduce columns with group names to focus on the specific part of
  comments/summary
- Output streaming, because LLM is slow
- Defend from the possible prompt injections in the comments.
- Generation quality is unstable. Need to improve.
-
