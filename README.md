# ESF Add-ons automation repository

This repository contains GitHub actions and reusable workflows used for automating the development of the Everyware Software Framework (ESF) add-ons.

## Project structure

### `.github/workflows` folder

The `workflows` folder contains the reusable Github workflows. They're easily identified by the `_shared-*` identifier.

### `samples` folder

The `samples` folder contains the samples of workflows that can be added to a repository to use the actions and workflows in this repository.

In other words: in order to use one of the re-usable workflows contained in the `workflows` folder, the corresponding action file inside the `samples` folder need to be copied in the `.github/workflows` folder of the target repository.

### `config` folder

The `config` folder contains the configuration/template files needed by the re-usable workflows.
