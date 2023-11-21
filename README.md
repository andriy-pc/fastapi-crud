# Simple CRUD

Simple CRUD project using: 
* Python 3.11 
* FastAPI
* SQLAlchemy
* SQLLight 
* Pydantic 
* PDM
* aioprometheus

# How to set up project locally (MacOS)

```
brew install python@3.11
brew link python@3.11

curl -sSL https://raw.githubusercontent.com/pdm-project/pdm/main/install-pdm.py | python3 -
export PATH=$PATH:$HOME/.local/bin

pdm venv create 3.11
source .venv/bin/activate
pdm install --dev
```
