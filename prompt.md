# A Dummy Web Application for Note Taking: Generation Prompt

You should create a very simple note taking web application based on Django. The goal of the application is not note-taking, but to serve as a dummy web application for testing new deployment methods and platforms. The application should have the following features:

- The initial page should be the login page, where users can log in with their credentials. If the user does not have an account, they should be able to register for a new account.
- After logging in, the user should be redirected to a page where they can see a list of notes. From there, they can create, view, edit, export and delete notes. Each note should have a title and a date. The notes should be stored in a PostgreSQL database.
- Every time a note is created or we click on it to edit it from the note list page, a new page is opened, where the user can edit the note. The note should be saved automatically when the user clicks outside the text area or when they click on a "Save" button.
- The application should have a clean and simple user interface, with a focus on usability and performance.

Tech stack and requirements:

- Web engine: Django (Python >= 3.12)
  - Use Django's built-in authentication system for user management
  - Use Django's built-in migration system for database management
- WSGI server: Gunicorn
- Database: PostgreSQL
- Environment and package management: `uv` + `pyproject.toml`
- Testing: `nox` with `black` + `pylint` + `mypy` + `pytest`
  - Write unit tests; mock the database by creating en ephemeral PostgrSQL database.
- CI/CD: use Github Actions for CI/CD, every PR to `main` should trigger a CI/CD pipeline that runs tests
- Deployment preparation:
    - The Django webapp should be packed into a Dockerfile.
    - We should have a `docker-compose.yaml` where both the Django image as well as the PostgreSQL database are instantiated and the app is started.
    - The docker-compose should also have an `nginx` service which works as reverse proxy; the configuration file and/or scripts should be created and applied to it, too. The `nginx` node is optional: make possible to operate without it.

Further requirements:

- Document the architecture and basic usage in the `README.md` file; use code blocks if necessary, as well as mermaid diagrams.
- The code should be inside the folder `src`.
- The tests should be in the folder `tests` at root level, not inside `src`.

Do as follows:

- Read this specification file and think of any missing important definition.
- Create a `SPEC.md` file where a complete specification is done.
- Load the `SPEC.md` and plan the implementation.
- Go step by step through the implementation plan until the application is developed.
- Use the tests you write and verify all your implementations.

Remember, this web application should be simple, but professional. The goal of the application is not the application itself, but I want to use it as a template/dummy repository to try new deployment methods and platforms.
