from slack_bolt import App
from slack_bolt.context.say.say import Say
from slack_bolt.adapter.socket_mode import SocketModeHandler
from azureCore import VmCore

class SlackCore(VmCore):
    def __init__(self) -> None:
        super().__init__()
        self.app = App(token=self.credentials["SLACK_BOT_TOKEN"])
        self.app.event("app_mention")(self.handle_app_mention)

    def handle_app_mention(self, body: dict, say: Say,) -> None:                             
        if "help" in body["event"]["text"]:
            say("""
```
1. help - Shows this help message        

2. init - Initializes the Resource Group for You            
    - Usage: init <resource group name>
3. list - Lists all the virtual machines   
    - Usage: @CloudBot list             
4. create - Creates a virtual machine 
    - Usage: @CloudBot create <vm_name> <nic_name> <subnet_name> <vnet_name> <username> <location>
5. start - Starts a virtual machine 
    - Usage: @CloudBot start <vm_name>
6. stop - Stops a virtual machine
    - Usage: @CloudBot stop <vm_name>    
7. status - Shows the status of a virtual machine
    - Usage: @CloudBot status <vm_name>
8. delete - Deletes a virtual machine
    - Usage: @CloudBot delete <vm_name>
```
""")             
        elif "list" in body["event"]["text"]:            
            try:
                say(self.list_all_vms(body["event"]["user"]))
            except Exception as e:
                say(f"Error Occured: {e}")
                say("Error Rectification:\n1. Check if the Resource Group is initialized\n")
        elif "create" in body["event"]["text"]:
            try:                
                status = self.provision_vm(
                    group_name=body["event"]["user"],
                    vm_name=body["event"]["text"].split(" ")[1],
                    nic_name=body["event"]["text"].split(" ")[3],
                    subnet_name=body["event"]["text"].split(" ")[4],
                    vnet_name=body["event"]["text"].split(" ")[5],
                    username=body["event"]["text"].split(" ")[6],
                    location=body["event"]["text"].split(" ")[2],
                )               

                say(
                    f"""
                    ```
                    Virtual Machine Created Successfully\n
                    Virtual Machine Name: {status["vm_name"]}\n
                    Virtial Machine ID: {status["vm_id"]}\n
                    Virtual Machine Location: {status["vm_location"]}\n
                    Virtual Machine Size: {status["vm_size"]}\n
                    Virtual Machine Username: {status["vm_username"]}\n
                    Virtual Machine Password: {status["vm_password"]}\n
                    Virtual Machine Public IP: {status["vm_public_ip"]}\n
                    Virtual Machine Private IP: {status["vm_private_ip"]}\n
                    ```
                    """
                )
            except Exception as e:
                say(f"Error Occured: {e}")
                say("Error Rectification:\n1. Check if the Resource Group is initialized\n")
        elif "start" in body["event"]["text"]:
            try:
                say(self.start_vm(body["event"]["user"], body["event"]["text"].split(" ")[1]))
            except Exception as e:
                say(f"Error Occured: {e}")
                say("Error Rectification:\n1. Check if VM is stopped\n")
        elif "stop" in body["event"]["text"]:
            try:
                say(self.stop_vm(body["event"]["user"], body["event"]["text"].split(" ")[1]))
            except Exception as e:
                say(f"Error Occured: {e}")
                say("Error Rectification:\n1. Check if VM is running\n")
        elif "status" in body["event"]["text"]:
            try:
                say(self.vm_status(body["event"]["user"], body["event"]["text"].split(" ")[1]))
            except Exception as e:
                say(f"Error Occured: {e}")
                say("Error Rectification:\n1. Check if VM is running\n")
        elif "delete" in body["event"]["text"]:
            try:
                say(self.delete_vm(body["event"]["user"], body["event"]["text"].split(" ")[1]))
            except Exception as e:
                say(f"Error Occured: {e}")
                say("Error Rectification:\n1. Check if VM is running\n")
        
        else:
            say("Type **@CloudBot help** for more information")

    def run(self) -> None:
        SocketModeHandler(self.app, self.credentials["SLACK_APP_TOKEN"]).start()

if __name__ == "__main__":
    SlackCore().run()
