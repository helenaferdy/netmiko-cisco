from lib.getCustom.device import Routers, ERROR_COMMAND
import threading
import os
import yaml

TITLE = "getCustom"
TESTBED =  "testbed/device.yaml"
CUSTOM_FILE = "import/custom.txt"
devices = []
custom_commands = []
success_counter = []

def main():
    read_testbed()
    create_folder_1()
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
    device.out_path = f"out/{TITLE}/"
    device.log_path = f"log/{TITLE}.log"
    device.errorlog = f"log/error/{TITLE}-error.log"
    device.create_folder()
    if device.connect(i):
        success_counter.append(0)
        for command in custom_commands:
            output = "Function exception"
            while output == "Function exception" and device.exception_counter < 3:
                output = device.connect_command(command)
        
            if [c for c in ERROR_COMMAND if c in output]:
                device.logging_error(f"{device.hostname} : Output return empty for command [{command}]")
            else:
                device.export_data_custom(command, output)

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

def create_folder_1():
    outpath = f'out/{TITLE}/'
    if not os.path.exists(outpath):
        os.makedirs(outpath)

def read_custom_commands():
    with open(CUSTOM_FILE, "r") as f:
        for csv_command in f:
            custom_commands.append(csv_command.strip())