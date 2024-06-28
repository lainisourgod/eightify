# 🦉 Eightify

> [eightify.app](https://eightify.app) clone with a new feature explored

## 👽 Description (wanna-be)

- ⏱️ Save time on long videos, get key ideas instantly
- 📚 Eightify helps when you're swamped with too much content
- 🧠 It's an AI YouTube tool which finds the key points in topics like AI,
  Business, Finance, News, or Health
- 🚀 Eightify boosts your learning
- 🎯 Grasp the gist of any video in seconds with our YouTube summary AI
- _**NEW**_ 📈 Get insights from comments at breeze with the comment groups
- 🔍 Navigate through videos with ease using summarized paragraphs with
  timestamps
- 💡 Get the pivotal points and key ideas from the video
- 🌍 Access translations of summaries in your preferred language. No more
  language barriers with Eightify!

![main page](./img/main_page.jpg)

- [🦉 Eightify](#-eightify)
  - [👽 Description (wanna-be)](#-description-wanna-be)
  - [👾 Why do this](#-why-do-this)
  - [🎼 System design](#-system-design)
    - [💘 General pipeline](#-general-pipeline)
    - [👹 Design decisions](#-design-decisions)
    - [💸 Unit economics](#-unit-economics)
  - [👻 Usage](#-usage)
  - [🧑‍💻 Development](#-development)
  - [🏗️ Project structure](#️-project-structure)
  - [🤩 TODO:](#-todo)

## 👾 Why do this

- 😶‍🌫️ My main focus in this app was to add a comment analyzer feature because it
  was lacked in the app. They only show one-sentence TLDR and show comments in
  the exact order that YouTube shows them.
- 💠 It's not really interesting, but there's **so much** insights hidden in the
  comments section. Like, is there any manipulations by the political speaker in
  the interview, or any personal stories.
- 💖 I personally sometimes spend more time reading the comments than watching
  the actual video, or read comments before starting the video, and if there was
  a tool that could help me reliably do that analysis, I'd pay for it even more
  than for video summarizer
- I wouldn't use the app at the current development state, but it's a nice PoC
  that this could really work.

## 🎼 System design

### 💘 General pipeline

- Get the video description, transcript, comments from YouTube API
- Summarize the video using LLM
- Render the summary and ask for user's interest in the comments
- Feed the given summary, video description and comments to the LLM
- Auto-cluster the topics of the comments in one pass to LLM: ask to both find
  topics and assign each comment to the topic
- Render the comment analysis grouped by comment topics to quickly filter this
  mess

### 👹 Design decisions

- I use raw calls to OpenAI API instead of LLM framework because I don't want an
  unnecessary complexity for the MVP
- I set the desired format for the summary and comment analysis with OpenAI's
  function calling. Like this

  ```python
      Provide the summary as a JSON array of objects. Each object should have the following structure:
    {{
        "emoji": "Relevant emoji",
        "title": "Bold title (max 5 words)",
        "content": "Concise paragraph combining main idea, practical implications, and examples",
        "quote": "Brief, impactful quote from the video",
        "timestamp": "Approximate timestamp (MM:SS format)"
    }}

    ............................................................................................

    {{
        "topics": [
            {{"name": "Topic Name", "description": "Brief description of the topic"}}
        ],
        "comment_assignments": [
            {{"comment_index": 0, "topic_index": 0}}
        ],
        "overall_analysis": "Your overall analysis of the comments and topics"
    }}
  ```

  LLMs are actually pretty good at following the format using function calling
  or other means of structured generation (like
  [outlines](https://github.com/outlines-dev/outlines)).

- I wrote a disgustingly long system prompt trying to achieve the best possible
  summary quality. "How would I summarize the video myself"? Problems I tried to
  solve:

  - **Boring**, boilerplate, robotic, timewasting, filler: content that I
    wouldn't want to read
  - **Reliability/Recall**: I want to be sure I'm not missing anything important
  - **Precision**: AI didn't make things up
  - **Filtering**: Find real gems down there

    This ain't the best solution to the problem, but prompt engineering is at
    the core of that business → would be improved iteratively.

- 😒 I don't support translations and non-English language videos at the moment.
  Because we need to write a correct logic on which transcript to fetch:
  - Is manually generated in Deutch better than auto-recognized English?
  - Is manually generated Russian better than auto-translation from Russian to
    English for our model?
  - Should we output in English either way or introduce other language to the
    prompt? We need to separately test this functionality

### 💸 Unit economics

- gpt-4o costs $5/mln input + $15/mln output tokens
- For [this 15-minutes long video](https://www.youtube.com/watch?v=O0H2m_r-ZhI)
  we have 10k input tokens and 1k output tokens. This includes both system
  prompt and user prompt for summary and comment analysis.
- The cost of one video summary is then: $0.05 + $0.015 = 7 cents per video 🐜
- Let's assume we charge $4/user/month, average user summarizes 20 videos per
  month and 50% of the summarized videos are watched by more than one user
- 20 \* 0.5 \* 0.07 = $0.7 per user. Seems good for short videos. We can even
  pay our developers and AWS bills 🤗

## 👻 Usage

- Install in venv
  `python -m venv .venv && source .venv/bin/activate && pip install -r requirements.lock`
- Put creds in `.env`
- Start the backend in one terminal: `fastapi run src/eightify/main.py`
- Start the frontend in another terminal: `streamlit run src/eightify/app.py`
- Enjoy your time in the browser interface:
  [http://localhost:8501](http://localhost:8501)

## 🧑‍💻 Development

- Install rye — yet another package manager, but from the creators of ruff:
  `curl -sSf https://rye.astral.sh/get | bash`
- Install env `rye sync`
- Install pre-commit hooks: `pre-commit install`
- Put creds, override config params in `.env`
- Run tests: `rye run pytest`
- Test backend from swagger docs: `127.0.0.1:8000/docs`

## 🏗️ Project structure

- `main.py` — backend on FastAPI
- `app.py` — fronted on Streamlit
- `api/youtube.py` — API calls to YouTube (descriptions, transcripts, comments)
- `api/llm/base.py` — interaction with LLM, system prompt, debug logs
- `api/llm/summary.py` — summary prompt and response parsing
- `api/llm/comments.py` — comments prompt and response parsing
- `config.py` — configuration with `pydantic-settings`
- `common.py` — common types used in different parts of backend and frontend

## 🤩 TODO:

- Dockerize
  - Will use the same Dockerfile for the backend and frontend as they share the
    common logic
  - Add docker-compose
- **Add demo deployment** (Github Pages?)
  - create a separate openai token for the demo with limited quota
  - show exceptions if token limit is reached
  - add notification to telegram when somebody is using the demo?
- Migrate to LLM framework (langchain / haystack / dspy)
- Automatic evaluation pipeline using LLM framework (too much to implement
  myself)
- Optimize the prompt. Currently it's 8k tokens of input and the result is not
  the best it can be...
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
- Output streaming, because LLM is slow
- Defend from the possible prompt injections in the comments.
- Generation quality is unstable. Need to improve.
- Make UI more accessible — line lengths, font sizes, emojis, structure, etc.
- Create some predefined categories for the comments. Like "personal stories",
  "surprising", "critique" etc
- Download user names, likes, favicons and show in UI
- In UI we can add hyperlinks from comment found in the group to the comment on
  YouTube (to read replies etc)
