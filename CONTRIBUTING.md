# Contributing

## Setup
```bash
git clone <repo>
cd weather-pipeline
make install        # installs deps + pre-commit hooks
cp .env.example .env
```

## Daily workflow
```bash
make test           # run tests
make run            # run pipeline
make lint           # check linting
make format         # fix formatting
git commit          # pre-commit hooks run automatically
```

## Adding dependencies
```bash
uv add <package>            # runtime dep
uv add --dev <package>      # dev dep
# commit both pyproject.toml and uv.lock together
```
