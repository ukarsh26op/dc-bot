# Discord Minecraft Control Bot

This bot controls one Pterodactyl server through the Pterodactyl Client API.

Commands:
- /startserver
- /stopserver
- /restartserver
- /status
- /testapi

## GitHub Codespaces setup

1. Create a new GitHub repository.
2. Add these files.
3. Create a `.env` file from `.env.example`.
4. Fill in the environment variables.
5. Run:

   python3 -m pip install -r requirements.txt
   python3 bot.py

Keep `.env` out of GitHub.

## Important

The bot needs a reachable PANEL_URL. If your Pterodactyl Panel is only available inside a Codespace and its forwarded URL changes, update PANEL_URL accordingly.

The bot does not directly control Wings. Pterodactyl Panel receives the API request and tells Wings to perform the power action.
