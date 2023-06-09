from lib.getCRC.device import Routers, TIMESTAMP
import csv
import threading
import os
import yaml

COMMAND1 = "show interfaces"
COMMAND2 = "show int"
HEADERS = ['No', 'Hostname', 'Interface', 'CRC', 'Input Errors', 'Output Errors']
ERROR_COMMAND = ['Invalid input', 'No such process', 'Incomplete command', 'Unknown command', 'Ambiguous command']
TESTBED =  "testbed/device.yaml"
OUTPATH = "out/getCRC/"
TEMPLATE_NUMBERS = 1
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
    num_try = 0
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
                parsed = device.parse(COMMAND1, output, num_try)
        
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