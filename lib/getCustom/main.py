from lib.getCustom.device import Routers, TIMESTAMP
import threading
import yaml


ERROR_COMMAND = ['Invalid', 'No such process', 'Incomplete', 'Unknown', 'Ambiguous', 'subcommands']
TESTBED =  "testbed/device.yaml"
OUTPATH = "out/getCustom/"
CUSTOM_FILE = "import/custom.txt"
devices = []
custom_commands = []
success_counter = []

def main():
    read_testbed()
    read_custom_commands()
    i = 1
    threads = []
    for device in devices:
        t = threading.Thread(target=process_device, args=(device, i))
        t.start()
        threads.append(t)
        i += 1

    for t in threads:
        t.join()

    print(f'\n=========> [{len(success_counter)}/{len(devices)}] devices successfully executed\n')

def process_device(device, i):
    device.create_folder()
    if device.connect(i):
        success_counter.append(device.hostname)
        for command in custom_commands:
            output = device.connect_command(command)
        
            if [c for c in ERROR_COMMAND if c in output]:
                device.logging_error(f"{device.hostname} : Output return empty for command [{command}]")
            else:
                device.export_data(command, output)

        device.disconnect()


def read_testbed():
    with open(TESTBED) as f:
        device = yaml.safe_load(f)['devices']
        for d in device:
            the_ip = device[d]['connections']['cli']['ip']
            the_protocol = device[d]['connections']['cli']['protocol']
            the_username = device[d]['credentials']['default']['username']
            the_password = device[d]['credentials']['default']['password']
            the_enable = device[d]['credentials']['enable']['password']
            the_ios_os = device[d]['os']

            new_device = Routers(
                d,
                the_ip,
                the_username,
                the_password,
                the_enable,
                the_ios_os,
                the_protocol
            )
            devices.append(new_device)

def read_custom_commands():
    with open(CUSTOM_FILE, "r") as f:
        for csv_command in f:
            custom_commands.append(csv_command.strip())