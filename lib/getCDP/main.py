from lib.getCDP.device import Routers, TIMESTAMP
import csv
import threading
import os
import yaml

COMMAND1 = "show cdp neighbors"
COMMAND2 = "show cdp neighbor"
COMMAND_PLATFORM = "show platform"
HEADERS = ['No', 'Local Hostname', 'Local Interface', 'Local Platform', 'Remote Hostname', 'Remote Interface', 'Remote Platform', 'Capability']
ERROR_COMMAND = ['Invalid', 'No such process', 'Incomplete', 'Unknown', 'Ambiguous']
TESTBED =  "testbed/device.yaml"
OUTPATH = "out/getCDP/"
TEMPLATE_NUMBERS = 1
TEMPLATE_NUMBERS_PLATFORM = 2
devices = []
success_counter = []

def main():
    read_testbed()
    export_headers()
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
    parsed = ""
    parsed_platform = ""
    num_try = 0
    num_try_p = 0
    device.create_folder()
    if device.connect(i):
        command = COMMAND1
        output = device.connect_command(command)

        #try other command
        if [c for c in ERROR_COMMAND if c in output]:
            device.logging_error(f"{device.hostname} : Command [{command}] Failed, trying [{COMMAND2}]")
            command = COMMAND2
            output = device.connect_command(command)
        
        #final check output
        if [c for c in ERROR_COMMAND if c in output]:
            device.logging_error(f"{device.hostname} : Output return empty for command [{command}]")
        else:
            while parsed == "" and num_try < TEMPLATE_NUMBERS:
                num_try += 1
                parsed = device.parse(command, output, num_try)
        
        ## GET PLATFORM
        output_platform = device.connect_command(COMMAND_PLATFORM)
        if [c for c in ERROR_COMMAND if c in output_platform]:
            device.logging_error(f"{device.hostname} : Output return empty for command [{COMMAND_PLATFORM}]")
        else:
            while parsed_platform == "" and num_try_p < TEMPLATE_NUMBERS_PLATFORM:
                num_try_p += 1
                parsed_platform = device.parse(COMMAND_PLATFORM, output_platform, num_try_p)
        if parsed_platform != "":
            device.platform = parsed_platform[0]['chassis']
    

        #special templates
        if parsed != "":
            device.export_csv(parsed)
            success_counter.append(device.hostname)
        else:
            device.logging_error(f"{device.hostname} : Parsing failed after [{num_try}] tries.")

        device.disconnect()

def export_headers():
    if not os.path.exists(OUTPATH):
        os.makedirs(OUTPATH)

    with open(f"{OUTPATH}{COMMAND1}_{TIMESTAMP}.csv", 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(HEADERS)

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
                the_protocol,
                COMMAND1
            )
            devices.append(new_device)