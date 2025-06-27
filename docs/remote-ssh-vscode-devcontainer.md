# VSCode Remote SSH and DevContainer Setup Guide

WARNING: It is recommended for developers to understand containerization, docker setup and builds.
Tradeoff here is, developer skills vs VM cost. If developer skills are not possible only options remains is to setup a vm for development. It is costlier because you are paying for a developer as well as a VM.

## Prerequisites

Before you begin, ensure you have the following:

- VSCode Installed: Download and install Visual Studio Code from the [official website](https://code.visualstudio.com/).
- SSH Client: Your system should have an SSH client installed (usually pre-installed on Linux/macOS; for Windows, you might need Git Bash or an OpenSSH client).
- Remote Server Access: You need access to a remote server with an IP address (e.g., `1.2.3.4`), a username (e.g., `ubuntu`), and an SSH private key (`.pem` file).

## Step 1: Install the Remote - SSH Extension

The Remote - SSH extension allows VSCode to connect to remote machines using SSH.

1. Open Visual Studio Code.
2. Go to the Extensions view by clicking the Extensions icon on the Activity Bar on the side of VS Code or by pressing `Ctrl+Shift+X` (Windows/Linux) or `Cmd+Shift+X` (macOS).
3. In the search bar, type `Remote - SSH`.
4. Find the extension published by Microsoft and click the Install button.

## Step 2: Configure SSH Host

You need to add your remote server details to your SSH configuration file, typically located at `~/.ssh/config` (Linux/macOS) or `%USERPROFILE%\.ssh\config` (Windows). This allows you to define aliases and specific connection parameters for your remote hosts.

1. Open a terminal (Linux/macOS) or Git Bash (Windows).
2. Navigate to your SSH directory:
```shell
cd ~/.ssh/
```
If the `.ssh` directory doesn't exist, create it:
```shell
mkdir ~/.ssh
chmod 700 ~/.ssh
```
3. Open or create the `config` file using a text editor (e.g., `nano`, `vim`, or VSCode itself):
```shell
nano config
```
or
```shell
code ~/.ssh/config
```
4. Add the following configuration block to the `config` file, replacing the placeholder values with your actual server details:
```
Host 1.2.3.4
  HostName 1.2.3.4
  User ubuntu
  IdentityFile ~/.ssh/privatekey.pem
  StrictHostKeyChecking no
  UserKnownHostsFile ~/.ssh/known_hosts
```
- `Host 1.2.3.4`: This defines an alias for your connection. You can use the IP address directly or choose a more descriptive name (e.g., my-frappe-server).
- `HostName 1.2.3.4`: The actual IP address or hostname of your remote server.
- `User ubuntu`: The username you use to log in to the remote server.
- `IdentityFile ~/.ssh/privatekey.pem`: The path to your private SSH key file. Make sure this file has the correct permissions (`chmod 400 ~/.ssh/privatekey.pem`).
- `StrictHostKeyChecking no`: (Optional, for initial setup convenience, but less secure) This setting prevents SSH from prompting you to confirm the host's authenticity on first connection. It's recommended to set this to yes or ask in production environments after the first successful connection.
- `UserKnownHostsFile ~/.ssh/known_hosts`: Specifies the file where known host keys are stored.
5. Save and close the config file.

## Step 3: Connect to the Remote Host

Now you can connect to your remote server directly from VSCode.

1. Open the Command Palette in VSCode by pressing `Ctrl+Shift+P` (Windows/Linux) or `Cmd+Shift+P` (macOS).
2. Type `Remote-SSH: Connect to Host...` and select the option.
3. VSCode will show a list of configured hosts. Select `1.2.3.4` (or whatever `Host` alias you defined).
VSCode will open a new window and attempt to establish an SSH connection to your remote server. You might be prompted for your SSH key passphrase if it has one.

## Step 4: Open Remote Folder

Once connected to the remote host, you can open a specific folder on that server.

1. With the new VSCode window connected to your remote host, open the Command Palette (`Ctrl+Shift+P` or `Cmd+Shift+P`).
2. Type `Remote-SSH: Open Folder...` and select the option.
3. A file explorer dialog will appear, showing the remote file system. Navigate to the desired folder, e.g., `/home/ubuntu/frappe_docker`.
4. Click OK.
The VSCode window will reload, and you will now be working directly within the `/home/ubuntu/frappe_docker` folder on your remote server.

## Step 5: Re-Open in DevContainer

If your remote folder contains a `.devcontainer` directory with a `devcontainer.json` file, you can re-open the workspace within a DevContainer. This provides a consistent and isolated development environment.

1. Make sure you have the Dev Containers extension installed (similar to Step 1, search for `Dev Containers` by Microsoft).
2. Once your remote folder `/home/ubuntu/frappe_docker` is open in VSCode, open the Command Palette (`Ctrl+Shift+P` or `Cmd+Shift+P`).
3. Type `Dev Containers: Reopen in Container` and select the option.
VSCode will now build (if necessary) and connect to the DevContainer defined in your `frappe_docker` project. This process might take some time for the first build. Once complete, you will have a fully functional development environment within the container, complete with all necessary dependencies and tools.
