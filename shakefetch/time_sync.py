import paramiko
from datetime import datetime

class ShakeCommunicator:
    def __init__(self, host, username, password):
        self.host = host
        self.username = username
        self.password = password
        self.client = None

    def connect(self):
        """Establishes an SSH connection."""
        if self.client and self.client.get_transport() and self.client.get_transport().is_active():
            # Already connected
            return "Already connected."
        try:
            self.client = paramiko.client.SSHClient()
            self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            self.client.connect(self.host, username=self.username, password=self.password, timeout=10)
            return "Connection successful."
        except Exception as e:
            self.client = None
            return f"Connection failed: {e}"

    def disconnect(self):
        """Closes the SSH connection."""
        if self.client:
            self.client.close()
            self.client = None
            return "Connection closed."
        return "Not connected."

    def is_connected(self):
        """Checks if the client is connected."""
        return self.client and self.client.get_transport() and self.client.get_transport().is_active()

    def set_time_utc(self):
        """Sets the remote host's time to the current UTC time."""
        if not self.is_connected():
            return "Not connected. Please connect first."

        date_now = datetime.utcnow().strftime("%d %b %Y %H:%M:%S")
        command = f'sudo -kS date --set "{date_now}"'

        try:
            stdin, stdout, stderr = self.client.exec_command(command)
            stdin.write(self.password + '\n')
            stdin.flush()

            output = stdout.read().decode()
            error = stderr.read().decode()

            result = ""
            if output:
                result += f"Output:\n{output}\n"
            if error:
                result += f"Error:\n{error}\n"
            if not result:
                result = "Time synchronization completed successfully, no output."
            return result
        except Exception as e:
            return f"An error occurred during time synchronization: {e}"

def connect_and_set_time(host, username, password):
    """
    Connects to a remote host, sets the time, and disconnects.
    """
    shake = ShakeCommunicator(host, username, password)
    connection_result = shake.connect()
    if "successful" not in connection_result:
        return connection_result

    sync_result = shake.set_time_utc()
    shake.disconnect()
    return sync_result
