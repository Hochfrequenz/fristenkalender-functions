# fristenkalender-functions

This repository is a collection of [Azure Functions](https://docs.microsoft.com/en-us/azure/azure-functions/) that
expose the features of [fristenkalender_generator](https://github.com/Hochfrequenz/fristenkalender_generator).

## List of Functions

| HTTP Method | Function Name                                                          | Purpose                                                                            | Parameter                              | Response                                            | localhost example                                                                                              |
|-------------|------------------------------------------------------------------------|------------------------------------------------------------------------------------|----------------------------------------|-----------------------------------------------------|----------------------------------------------------------------------------------------------------------------|
| GET         | [`GenerateAllFristen`](src/GenerateAllFristen)                         | generate all fristen for the given year                                            | a number                               | a JSON list, use `&concise=True` for compact output | test with [localhost:7071](http://localhost:7071/api/GenerateAllFristen/2023)                                  |
| GET         | [`GenerateAndExportWholeCalendar`](src/GenerateAndExportWholeCalendar) | Generates an ics-file for a given year, with a given filename and a given attendee | a number, file_name, and email address | an ics-file                                         | test with [localhost:7071](http://localhost:7071/api/GenerateAndExportWholeCalendar/calendar/test@test.com/2023) |
| GET         | [`GenerateFristenForType`](src/GenerateFristenForType)                 | generate fristen for a given type and a given year                                 | number and fristen type                | a JSON list                                         | test with [localhost:7071](http://localhost:7071/api/GenerateFristenForType/2023/GPKE)                         |

## Scope of the Fristenkalender Functions

The functions in this repository should contain only actual logic for
providing a HTTP interface to existing FristenkalenderGenerator functionality .

# Local Setup / Getting Started

You need to take two steps to get this repository running on your localhost:

1. install and setup the Azure Function framework
2. setup the Python virtual env

Please follow the official documentation
on [Python based Azure Functions](https://docs.microsoft.com/en-us/azure/azure-functions/create-first-function-cli-python)
for guidance on how Azure Function projects are structured and how to setup your local development environment.

For the Python part alone, just follow [the usual tox workflow](https://github.com/Hochfrequenz/python_template_repository#how-to-use-this-repository-on-your-machine).

Once you completed the general Azure Function setup, go into the src directory and run

```bash
func start
```

### Troubleshooting

As of 2023-07-13 Azure Function [only supports](https://docs.microsoft.com/en-us/azure/azure-functions/functions-reference-python?tabs=asgi%2Cazurecli-linux%2Capplication-level#python-version) Python <=v3.9.

In case your local tox base uses Python v3.10 (and you cloned this repo before 2022-04-04), you'll run into an error if you try to start the Azure Function (the plain Python unit tests will behave normally, though):

> Found Python version 3.10.0 (py).
> Python 3.6.x to 3.9.x is required for this operation. Please install Python 3.6, 3.7, 3.8, or 3.9 and use a virtual environment to switch to Python 3.6, 3.7, 3.8, or 3.9.

To pin tox to Python v3.9 we use the tox' `basepython` setting.
Re-create the dev environment, then try again.
