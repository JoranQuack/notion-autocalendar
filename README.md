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

Create Python Virtual Environment and install dependencies with [uv](https://github.com/astral-sh/uv)

```bash
  uv sync
```

Run the script

```bash
  uv run main.py
```

## Authors

- [@JoranQuack (me)](https://github.com/JoranQuack)
- [@ethanelliot (my pookie)](https://github.com/ethanelliot/)

## Roadmap

- Allow customisable URLs (with a variable number of them) and Notion parameters.
- Maybe develop a frontend app to leverage this functionality more generally.
