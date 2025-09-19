import paramiko
from datetime import datetime

def set_remote_time_utc(host, username, password):
    """
    Connects to a remote host via SSH and sets the date to the current UTC time.
    """
    date_now = datetime.utcnow().strftime("%d %b %Y %H:%M:%S")
    command = f'sudo -kS date --set "{date_now}"'
    with paramiko.client.SSHClient() as client:
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(host, username=username, password=password, timeout=10)
        stdin, stdout, stderr = client.exec_command(command)
        stdin.write(password + '\n')
        stdin.flush()
        output = stdout.read().decode()
        error = stderr.read().decode()
        result = ""
        if output:
            result += f"Output:\n{output}\n"
        if error:
            result += f"Error:\n{error}\n"
        if not result:
            result = "Operation completed successfully, no output."
        return result
