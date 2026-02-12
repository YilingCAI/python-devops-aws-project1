This is the backend installation

```bash install pyenv and python
echo 'eval "$(pyenv init --path)"' >> ~/.zprofile\necho 'eval "$(pyenv init -)"' >> ~/.zshrc
cat ~/.zprofile
source ~/.zshrc
pyenv install 3.12.1
pyenv local 3.12.1
pyenv versions. # list all python versions
```

```bash install poetry 
brew install poetry
poetry --version
poetry config virtualenvs.in-project true
poetry init
poetry install --no-root
poetry env info
poetry run which python
```

```bash install package using poety
poetry add requests
poetry add --group dev pytest black ruff
poetry install #install all pacckage in pyproject.toml
poetry add pydantic-settings
```

```bash initialize alembic
poetry run alembic init alembic
poetry run alembic revision --autogenerate -m "create initial tables"
alembic upgrade head
```
