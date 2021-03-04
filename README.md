# pyhsieh-website-backend
Repository for maintaining personal website's backend.

## Installation
### Non-Pip Dependencies
 - `Python 3.8`. For development, it would be better to set up virtual environment with
   [`venv`](https://docs.python.org/3/library/venv.html) or [`pyenv`](https://github.com/pyenv/pyenv) +
   [`pyenv-virtualenv`](https://github.com/pyenv/pyenv-virtualenv)
 - `PostgreSQL 13.0`. You'll need to set up database and user with full access to that database. If you want to run
   unit tests, then you'll need to create another database, and grant full access to the same user.

### Pip Package Dependencies
Package dependencies and installation are managed by [`pip-tools`](https://github.com/jazzband/pip-tools).
You can directly run `make init-dev` or `make init-prod` to get them done at once, depends on the environment.

You may get errors which failed to link external libraries (for instance, `psycopg2`). While some of them can be solved
by installing the package globally, try finding link/include directory path, then pass `LDFLAGS`, `CPPFLAGS`, or
`CFLAGS` as environment variables before the command.
```
LDFLAGS="..." CPPFLAGS="..." make init-dev
```

Some of the dev-environment dependencies are optional, and you may want to add up some additional dependencies.
Package dependencies are listed in `requirements/dev.in` and `requirements/prod.in`. You can modify the lists,
then run `make update-dev` at repository root directory to update packages at once.

### Image Directories
In this application, original image and resized images are stored in separated directories, and assumes that website
server (in my case it's [pyhsieh-website-frontend](https://github.com/pykenny/pyhsieh-website-frontend)) can only access
the later directory. This can be achieved by assigning the two directories in different groups, and let the user who
runs the server be in both groups, and assuming the website server's in the group that owns the opened image directory
but not the other one.

In development environment, you can bypass this by passing the same group or even the same directory for both image
groups/directories. But for deployment you'll need to follow the above mechanism to protect original images from
getting exposed.

To run unit tests, you'll need extra group and directory settings for testing purpose. Again, you can just create one
more directory for testing, and assign them to the same group you use to run the dev-server. However, do not assign the
original dev-server directories to test image directory -- all files under test directories will be fully removed after
each test run that stores images, and images stored during development will be affected.

Check out the next section to get a better sense about what you need to set up.

### Environment Variable File
Most credentials and non-`django`-specific settings are managed out of `django`'s `settings.py` script. You should set
up a `.env` file under `blog_backend` directory to specify these settings. These settings will be loaded as environment
variables and then read and saved into `settings.py`. (This configuring method is suggested by
[Twelve-Factor App](https://12factor.net/config).)

The text below shows all these settings. Of course, you can set up these values by modifying `settings.py` directly,
but just keep in mind it's highly recommended to keep security information separated.

```shell script
SECRET_KEY="Place Your django Secret Key Here"

# Image directory settings
OPENED_IMAGE_GROUP="Group Name for Opened Images"
PROTECTED_IMAGE_GROUP="Group Name for Protected Images"
OPENED_IMAGE_DIR="Directory for Opened Images"
PROTECTED_IMAGE_DIR="Directory for Protected Images"

# Development environment only, if you need to run unit tests
OPENED_IMAGE_GROUP_TEST = "Group Name for Opened Images in Unit Test"
PROTECTED_IMAGE_GROUP_TEST = "Group Name for Protected Images in Unit Test"
OPENED_IMAGE_DIR_TEST = "Directory for Opened Images in Unit Test"
PROTECTED_IMAGE_DIR_TEST = "Directory for Protected Images in Unit Test"

# django-specific settings
DEBUG=0 # 0: False; 1: True

DB_NAME="Database's Name"
DB_TEST_NAME="Test Database's Name"
DB_USER="DB User Name"
DB_PASSWORD="DB User Password"
DB_HOST="Host Address or Socket Directory"
DB_PORT="DB Port"

LOG_DIR="Directory for storing log files (prod mode)"
LOG_BASE_NAME="Base name for log files (prod mode)"

CACHE_DIR="Directory for file-based cache (prod mode)"

ALLOWED_HOSTS="Comma-separated List. e.g.: localhost,127.0.0.1,www.mysite.com"
```

### Database Initialization
Run `scripts/manage migrate` under repository root directory to initialize database.

## Django Manage Command
`scripts/manage` provides an executable to save you few key strokes.

For instance, if you want to use `runserver` command to set up test server, then you can run this command at this 
repository's root directory:
```bash
> scripts/manage runserver [OPTIONS...]
```

## Style/Type Checking And Hooks
This application uses [`black`](https://github.com/psf/black), [`flake8`](https://github.com/PyCQA/flake8), and
[`mypy`](http://mypy-lang.org/) to enforce code styling and type notation.

A pre-commit git hook can be found in `git_hooks/pre-commit` and you can clone it by running
`make clone-pre-commit-hook` to `.git/hooks/`. This will run all the tools on added/modified Python files before
commits, and stop the process if any of them reports error.

If you want to run these tools on the whole repository, run `make black-all`,
`make flake8-all`, or `make mypy-all` under repository root.

## Tests
You can run tests by specifying targets and options through `scripts/manage`:

```bash
> scripts/manage test [OPTIONS...] resource_management.tests.service
```

To run all the tests at once:

```bash
> scripts/manage test_all [OPTIONS...]
```

If you want to run test directly through `manage.py` (`manage.py test`), remember to enable `--keepdb` option. This
application assumes that the database user does not have database creation privilege (creation and access granting
should done by some administrator atop.)

