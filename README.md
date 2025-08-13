# Notion AutoCalendar

A small Python project that automatically populates my Notion To-Do list database with events from the UC Moodle servers.

## Status

[![run main.py](https://github.com/JoranQuack/notion-autocalendar/actions/workflows/actions.yml/badge.svg)](https://github.com/JoranQuack/notion-autocalendar/actions/workflows/actions.yml)

## Acknowledgements

- [Ethan Elliot](https://github.com/ethanelliot/) - Inspiration, mentor, and pookie.

## Environment Variables

To run this project, you will need to add the following environment variables to your .env file

`NOTION_TOKEN`,
`NOTION_DATABASE_ID`,
`QUIZ_URL`,
`LEARN_URL`

## Run Locally

Clone the project

```bash
  git clone https://github.com/JoranQuack/notion-autocalendar
```

Go to the project directory

```bash
  cd notion-autocalendar
```

Create Python Virtual Environment (you will need Python3 installed)

```bash
  # MacOS/Linux
  # You may need to run `sudo apt-get install python3-venv` first on Debian-based OSs
  python3 -m venv .venv
  source .venv/bin/activate

  # Windows
  # You can also use `py -3 -m venv .venv`
  python -m venv .venv
  .venv\Scripts\activate

```

Install dependencies (requires pip to be installed)

```bash
  pip install -r /path/to/requirements.txt
```

Run the script

```bash
  python main.py
```

## Authors

- [@JoranQuack (me)](https://github.com/JoranQuack)
- [@ethanelliot (my pookie)](https://github.com/ethanelliot/)

## Roadmap

- Allow customisable URLs (with a variable number of them) and Notion parameters.
- Maybe develop a frontend app to leverage this functionality more generally.
