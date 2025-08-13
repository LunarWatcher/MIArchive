
# Contribution guidelines

## Basic guidelines

### Use of generative AI is banned

Generative AI uses training data [based on plagiarism and piracy](https://web.archive.org/web/20250000000000*/https://www.theatlantic.com/technology/archive/2025/03/libgen-meta-openai/682093/), has [significant environmental costs associated with it](https://mit-genai.pubpub.org/pub/8ulgrckc/release/2?readingCollection=9070dfe7)[^1], and [generates fundamentally insecure code](https://doi.org/10.1007/s10664-024-10590-1). GenAI is not ethically built, ethical to use, nor safe to use for programming applications. When caught, you will be permanently banned from contributing to the project, and any prior contributions will be checked and potentially reverted. 

### Testing policies

Anything that can be tested automatically, should be tested, within reason.

If you write new functionality that can be tested, you should write tests for it. This is not a hard requirement, but tests are a massive help in ensuring stuff doesn't break down the line. 

### Git practices

No specific Git practices are used.

### Code style and naming conventions

Python code is written in accordance with PEP 8, unless it's convenient not to. This notably applies to text breaking. PEP 8 requires a max line width of 79 characters (72 for docstrings and comments), which is just short enough that a lot of stuff goes past that, especially in precisely strings. 

No style conventions are checked or forced automatically by formatters, largely because I have a bad track record with formatters doing everything except what I want them to do.

## Development setup

```
# You want a venv
python3 -m venv env
source ./env/bin/activate

# Then install dev requirements
pip3 install -r requirements.txt

# Set up local environment development use
python3 -m mia setup --developer
```

This creates `config.json`, which is used to actually run the server. This is the same file used in the production setup. Additionally, it creates `.env.dev`, a prerequisite to run the tests, as the config used in the tests are generated on the fly, which means the tests need to know what password to use.

### Running tests

As long as you have your environment set up, running the tests is as simple as
```
python3 -m pytest
```

This will run the entire test suite. To run specific tests or other pytest-related related questions, see pytest's documentation.

> [!warning]
>
> Never, ever change POSTGRES_DATABASE in .env.dev to a production database. The tests assume the database you provide it is exclusively used for mia unit tests, and wipes data stored in it as part of the testing.

## Creating issues and pull requests

For bug reports, questions, feature requests, or similar, use [Codeberg](https://codeberg.org/LunarWatcher/MIArchive/issues). 

For pull requests, you can open them on either GitHub or Codeberg, but using Codeberg is strongly encouraged. Although all the workflows run on GitHub to avoid throwing traffic at Codeberg's limited CI servers, these running is not a requirement, as I'll usually be doing manual testing anyway. This is not a huge project, and nothing is automatically released without a tag, so the tests not running automagically before merging isn't a huge deal.

[^1]: Full collection permalink: https://doi.org/10.21428/e4baedd9.9070dfe7 - each entry does not seem to have its own DOI, to my great personal annoyance
