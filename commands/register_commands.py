import dotenv
import httpx
import yaml

config = dotenv.dotenv_values()
TOKEN = config["DISCORD_BOT_TOKEN"]
APPLICATION_ID = "1212209513474695229"
URL = f"https://discord.com/api/v10/applications/{APPLICATION_ID}/commands"


with open("discord_commands.yaml", "r") as file:
    yaml_content = file.read()

commands = yaml.safe_load(yaml_content)
headers = {"Authorization": f"Bot {TOKEN}", "Content-Type": "application/json"}

for command in commands:
    response = httpx.post(URL, json=command, headers=headers)
    command_name = command["name"]
    print(f"Command {command_name} created: {response.status_code}")
