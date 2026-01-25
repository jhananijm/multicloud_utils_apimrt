import subprocess

def run_command(command):
    command=command.split()
    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if result.returncode != 0:
        print(f"Command Execution failed: {command}")
    else:
        return result.stdout.decode().strip()


private_key=run_command("lscrypt read -d apim-rt generate-credentials/certs/ssh-private-key")
public_key=run_command("lscrypt read -d apim-rt generate-credentials/certs/ssh-public-key")


data=f"public_key: |\n{public_key}\nprivate_key: |\n{private_key}"

print(data)